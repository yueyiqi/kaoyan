"""Stable HTTP ingress for the portable cluster; administrative control is authenticated."""
from __future__ import annotations
import base64
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import uuid

from kaoyan_cluster_coordinator import Coordinator


class GatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, code, body, headers=None):
        self.send_response(code)
        for key, value in (headers or {'Content-Type': 'application/json; charset=utf-8'}).items():
            if key.lower() not in ('content-length', 'connection', 'transfer-encoding', 'server', 'date'):
                self.send_header(key, value)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def handle_request(self):
        cluster = self.server.cluster
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) > 1 or self.headers.get('Transfer-Encoding'):
                return self.respond(400, b'{"status":"invalid_request_framing"}')
            length = int(lengths[0]) if lengths else 0
            if not 0 <= length <= 2 * 1024 * 1024:
                return self.respond(413, b'{"status":"payload_too_large"}')
            raw = self.rfile.read(length)
            if self.path.startswith('/_cluster/'):
                if self.path != '/_cluster/control' or self.command != 'POST' or not hmac.compare_digest(
                        self.headers.get('Authorization', ''), 'Bearer ' + cluster.config['token']):
                    return self.respond(403, b'{"status":"forbidden"}')
                result = cluster.control(json.loads(raw))
                return self.respond(200, json.dumps(result).encode())
            if self.path == '/api/ai/long-sentence-coach/status' and self.command == 'GET':
                # 配置文件修改测试：W1 后端探测 N6 本地 Ollama (qwen3:32b) 状态
                from kaoyan_w1_n6_llm_coach_backend import handle_coach_status
                return self.respond(200, json.dumps(handle_coach_status(), ensure_ascii=False).encode('utf-8'))
            if self.path == '/api/ai/long-sentence-coach' and self.command == 'POST':
                from kaoyan_w1_n6_llm_coach_backend import handle_coach_diagnose
                payload = json.loads(raw.decode('utf-8') if raw else '{}')
                res = handle_coach_diagnose(payload)
                code = 400 if res.get('status') == 'bad_request' else 200
                return self.respond(code, json.dumps(res, ensure_ascii=False).encode('utf-8'))
            if self.path in ('/api/health', '/api/ha/status'):
                with cluster.lock:
                    if not cluster.state:
                        raise RuntimeError('Uninitialized')
                    cluster.recover()
                    state = cluster.status()
                result = {'status': 'ok', 'db_engine': 'portable_sqlite',
                          'ha_mode': 'SINGLE_COORDINATOR_SYNCHRONOUS_REPLICAS',
                          'version': state['version'], 'tables_count': len(state['tables']),
                          'replicas_confirmed': sum(int(v['ok']) for v in state['acks'].values())}
                return self.respond(200, json.dumps(result).encode())
            request = {'method': self.command, 'path': self.path,
                'headers': dict(self.headers), 'body': base64.b64encode(raw).decode(),
                'client_ip': self.client_address[0], 'request_id': uuid.uuid4().hex}
            response = cluster.request(request)
            return self.respond(response['code'], base64.b64decode(response['body']), response['headers'])
        except (ValueError, json.JSONDecodeError):
            self.respond(400, b'{"status":"bad_request"}')
        except (BrokenPipeError, ConnectionResetError):
            pass  # ACK may be lost; client retries with the same idempotency key.
        except Exception:
            self.respond(503, b'{"status":"temporarily_unavailable","message":"Please retry with the same request key."}',
                         {'Content-Type': 'application/json', 'Retry-After': '2'})

    do_GET = do_POST = do_HEAD = handle_request


def main(path):
    config = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    cluster = Coordinator(config)
    server = ThreadingHTTPServer(('127.0.0.1', config['port']), GatewayHandler)
    server.cluster = cluster
    print(json.dumps({'listening': server.server_address, 'initialized': cluster.state is not None}), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main(sys.argv[1])
