# 第六轮系统代理隔离 / Cycle 6 proxy-independent transport
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] W1 默认 HTTPS 探针失败 ev:ev-0026，错误 WinError 10061；DNS 正常，urllib 读取的 HTTP/HTTPS 代理主机为拒接请求的 127.0.0.1。
边界：这是 Windows 客户端代理设置，不是原生库表服务退出；三机 RPC 与生产写入已通过。
修复：内部回环 RPC 显式 ProxyHandler({})，不依赖各 OS 的系统代理和 NO_PROXY；运维控制同样隔离。
公网探针显式直连并验证正常证书，记录 transport=direct；不修改用户全局代理、浏览器设置或安全配置。
验收：污染 http_proxy/NO_PROXY 后内部 RPC 仍直连成功；W1 原生 HTTPS 直连返回正确集群；修订源滚动部署并复核摘要。
English: isolate internal transport from OS proxies and distinguish direct-route TLS verification from the user's global proxy configuration.

## [IoC_Revision_vLiveFinal]
Status: VERIFIED（业务 RPC/显式直连范围）；ev:ev-0031～0036；未改变 W1 全局代理。
