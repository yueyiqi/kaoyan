# 05 · kaoyan.elenalyl.top 打不开 (ERR_CONNECTION_CLOSED) 根因与香港边缘回源方案

> Status: `IMPLEMENTED (服务器侧全部完成) / BLOCKED_EXTERNAL (clientHold + DNS 指向，需用户在阿里云控制台操作)`
> 探针脚本: 同目录 `05_...py` (经 CVM 干净视角探测，规避 M4 Clash fake-ip 污染)

## 1. 根因链 (实测，自上而下)

| 层 | 事实 (实测) | 后果 |
| :-- | :-- | :-- |
| L1 注册局 | `elenalyl.top` RDAP 状态 = `client hold`（万网实名审核未过，2026-10-23 新注册） | `.top` 根不下发该域名，公共 DNS (8.8.8.8/223.5.5.5) 返回 NXDOMAIN；仅 `dns1.hichina.com` 能答 |
| L2 本机 | M4 的 Clash fake-ip 先返回假 IP `198.18.1.94` 接住连接，随后真实解析失败 | 浏览器看到「服务器主动关闭连接」= `ERR_CONNECTION_CLOSED` |
| L3 安全组 | CVM→`8.163.29.42:80/443` 超时；仅 22/3389 放行 | 即使域名解析成功，HTTPS 也进不去 |
| L4 ICP 拦截 | 同端口 3389：`Host: kaoyan.elenalyl.top` → 403（网关返回，非 Caddy）；`Host: 127.0.0.1` → 200 | elena 在 **广州 (cn-guangzhou)**，阿里云按 HTTP Host/SNI 拦截未备案域名；开放 80/443 也不能解决 |

结论：**单靠开安全组无法让域名直连 elena**，必须与 `kaoyan.liuzengyu.top` 同构：走香港边缘免备案回源。

## 2. 方案（与 kaoyan.liuzengyu.top 同构）

```
浏览器 ─HTTPS→ 香港边缘 CVM Caddy(自动证书) ─Host=127.0.0.1→ elena:3389(Caddy) → 127.0.0.1:60231 (User=elena)
```

## 3. 已实施 (ev 见 task_brief)

- CVM `Caddyfile` 新增 `kaoyan.elenalyl.top { reverse_proxy 8.163.29.42:3389 { header_up Host 127.0.0.1 } }`，`caddy validate` 通过并已 reload；HTTP 请求返回 308 跳转 HTTPS。
- `https://kaoyan.liuzengyu.top` 经同链路实测 200 / 67777 字节首页。

## 4. 需您在阿里云控制台完成 (本机无阿里云 AK，无法代办)

1. **域名控制台**：完成 `elenalyl.top` 实名认证模板审核，使 `clientHold` 解除（RDAP 转为 `active`）。
2. **云解析 DNS**：把 `kaoyan` 的 A 记录由 `8.163.29.42` 改为 **`43.160.227.166`**（香港边缘）。

两项完成后，CVM Caddy 会自动签发 Let's Encrypt 证书，无需再改任何配置。
验证：运行同目录探针，`L1=active`、`L6_dns_points_to_edge=true`，再 `curl -I https://kaoyan.elenalyl.top`。

> 不需要再开放 elena 的 80/443 安全组；3389 已满足边缘回源。建议后续把回源端口改为专用端口并限制源 IP 为 `43.160.227.166`。

## 5. 当前可用入口

`https://kaoyan.liuzengyu.top/` （由 elena `User=elena` 进程承载）

## 6. 修订 v1.1 · 安全组放行后复测 (2026-10-23 13:07)

**用户已在阿里云 ECS `elena_1`（`cn-guangzhou`，安全组 `sg-7xvbs65eahqwn3ymw2f3`）入方向放行：** `TCP 80`、`TCP 443`（`0.0.0.0/0`），原有 `22`、`3389` 保留。

CVM 干净视角复测：

| 探针 | 结果 | 结论 |
| :-- | :-- | :-- |
| `80` + `Host: kaoyan.elenalyl.top` | 403 | 网关按域名拦截仍在 (未备案) |
| `80` + `Host: 127.0.0.1` | 200 | 回源口径有效 |
| `443` + SNI=`kaoyan.elenalyl.top` | TLS 通、200 (自签) | SNI 暂未被拦截，但不保证长期 |
| RDAP | `client hold` 未变 | 公共 DNS 仍 NXDOMAIN，正式域名仍不可达 |
| Let's Encrypt 多地验证节点 → `elena:443` | 已命中 tls-alpn-01 | 安全组 443 对公网生效 |

**本次修订实施：** `elena` 的 Caddy 改为
- `https://kaoyan.8.163.29.42.nip.io`：真实 Let's Encrypt，仅 `tls-alpn-01`（避开 80 端口 Host 拦截）。nip.io 公共可解析，不依赖 `clientHold`，可作为立即可用的直连 HTTPS 入口。
- `https://kaoyan.elenalyl.top`：同样 alpn；待 `clientHold` 解除并 DNS 指向后自动签发。
- 明文 `:80/:3389` 保留，供香港边缘 `Host=127.0.0.1` 回源。

**实测结果 (13:14)：** `kaoyan.8.163.29.42.nip.io` 的 Let's Encrypt 证书已签发，CVM 与 M4 访问均为 `200`、证书校验通过。`kaoyan.elenalyl.top` 的签发被 Let's Encrypt 自己报 `NXDOMAIN` 拒绝，直接证实 `clientHold` 是唯一剩余阻塞。

**未变的硬阻塞：** `kaoyan.elenalyl.top` 仍受 `clientHold` 限制，这是控制台实名审核，非服务器可修。

## 7. 修订 v1.2 · SNI 级 RST 拦截下钻与最终路由 (2026-10-23 13:21)

### 7.1 根因链下钻与实测定位

| 层级 | 实测证据 | 结论 |
| :--- | :--- | :--- |
| **L1 注册局** | `elenalyl.top` RDAP 状态持续为 `client hold`；公共 DNS（8.8.8.8/223.5.5.5 等）返回 NXDOMAIN（mihomo Status=3）；Let's Encrypt 在 CVM（59次日志）与 elena（12次）均因 NXDOMAIN 验证失败。 | 注册局根域不解析，公共权威 DNS 均不可达。 |
| **L2 本地/浏览器** | M4 开启 Clash fake-ip，将未解析域名先映射至 `198.18.1.94`；mihomo 向上游递归查询得到 NXDOMAIN 后即刻关闭 TCP 连接，导致 Firefox 呈现 `PR_END_OF_FILE_ERROR`，Chrome 呈现 `ERR_CONNECTION_CLOSED`。 | 客户端报错系本地 DNS fake-ip 遇真实 NXDOMAIN 后的断流表现。 |
| **L3 阿里云网关 SNI 定向拦截** | 从 CVM 以 `--resolve` 绕过 DNS 直接连接 `8.163.29.42:443` 实测：<br>1) SNI=`kaoyan.elenalyl.top` 时立即收到 TCP RST（Connection reset by peer）；<br>2) 对照组 SNI=`example-unfiled-test.top` 收到 Caddy 原生 TLS alert internal error（未被网关拦截）；<br>3) elena 本机回环测试 SNI=`kaoyan.elenalyl.top` 同样返回 Caddy 原生 TLS alert（非 RST）；<br>4) 13:07 该路径尚可拿到 200，13:21 已被注入 RST，证实为后置定向拦截；80 端口 Host=`kaoyan.elenalyl.top` 则恒定返回 403。 | 阿里云广州网关在 443 端口按 SNI 注入 TCP RST 阻断，非 Caddy 行为；80 端口亦按 Host 拦截。 |
| **L4 路径可行性推导** | 即使 `clientHold` 解除，将 A 记录直接指向 `8.163.29.42` 也必然失败（80 端口 403，443 端口 RST），除非完成境内 ICP 备案。唯一可行路线为：DNS A 记录指向香港免备案节点 `43.160.227.166`（CVM），CVM 以明文 HTTP 回源 `elena:3389` 并改写 `Host: 127.0.0.1`（已实测 200，不触发网关拦截）。CVM 侧配置已就绪，无需改动。 | 国内 ECS 直连必须 ICP 备案；免备案业务必须且仅能走香港 CVM 边缘回源。 |
| **L5 elena 配置优化与限流防御** | elena 上的 `https://kaoyan.elenalyl.top` 站点块因外部流量无法到达已属无效配置，且其持续与 CVM 向 Let's Encrypt 申请签发会累积失败配额触发 ACME Rate Limit，拖慢后续 CVM 证书签发。 | 必须下线 elena 上的无效 HTTPS 站点块以规避 ACME 限流。 |

### 7.2 最终拓扑架构

```
浏览器 ─HTTPS→ 43.160.227.166 Caddy(自动申请证书) ─Host=127.0.0.1→ elena:3389 (Caddy) → 127.0.0.1:60231 (User=elena)
```

### 7.3 本次实施动作与存证

1. **elena Caddyfile 裁剪 (S1)**：
   - 备份旧配置至 `/etc/caddy/Caddyfile.bak.1792776232`；
   - 仅删除 `https://kaoyan.elenalyl.top { ... }` 站点块，完整保留 `:80/:3389` 明文回源块与 `https://kaoyan.8.163.29.42.nip.io` 独立证书块；
   - 经 `caddy validate` 校验合法后重新加载，`journalctl` 确认 `kaoyan.elenalyl.top` 的 obtain 尝试已完全终止。
2. **全链路断言存证 (S2 / S3)**：
   - 证据哈希入账：`ev:ev-0019`（`exit=0`, `verdict=met`）；
   - 经 CVM 视角实测：
     - a) `https://kaoyan.8.163.29.42.nip.io/` 返回 `200_0`（HTTPS 200，证书校验通过）；
     - b) `http://8.163.29.42:3389/`（`Host: 127.0.0.1`）返回 `200`（边缘回源通畅）；
     - c) `https://kaoyan.liuzengyu.top/` 返回 `200`（既有生产入口正常）；
     - d) `http://127.0.0.1/`（`Host: kaoyan.elenalyl.top`）返回 `308`（CVM 边缘重定向块存活）。

### 7.4 勘误与更正声明

> [!WARNING]
> **结论作废更正**：v1.1 中关于「A 记录可保持指向 `8.163.29.42` 直连」的推论已被 13:21 捕获的 SNI RST 物理证据证伪，该直连建议正式作废。国内广州 ECS 未备案前严禁作为主域名 A 记录解析目标。

### 7.5 用户后续待办 (外部阻塞)

1. **阿里云域名控制台**：完成 `elenalyl.top` 域名实名认证审核，促使注册局解除 `clientHold`（转为 `active`）；
2. **云解析 DNS 控制台**：将 `kaoyan` 的 A 记录修改为 **`43.160.227.166`**（香港边缘 CVM IP，**严禁指向 8.163.29.42**）；
3. **直连前置条件**：后续若需将流量直连 elena，必须为该广州 ECS 完成 ICP 备案，备案通过前切勿回切 A 记录。

### 7.6 运维注意事项

- **证书生效**：`clientHold` 解除后，CVM Caddy 会按退避重试算法自动签发 Let's Encrypt 证书；若解析生效后 30 分钟内仍未自动签出，可登录执行：
  ```bash
  ssh cvm "docker exec caddy-proxy caddy reload --config /etc/caddy/Caddyfile --force"
  ```
  *(注：切勿 `docker restart caddy-proxy`，该容器同时承载多个线上生产站点)*。
- **临时入口**：`https://kaoyan.8.163.29.42.nip.io/` 直连入口当前已签发可用，但国内网关亦存在后续将其 SNI 拦截的可能性，仅建议作为调试验证的临时备用入口。

## 8. 修订 v1.3 · A 记录已改为边缘后的最终根因与自动上线守护 (2026-10-23 13:35)

### 8.1 实测数据与层级定位 (13:35)

| 层级 | 探针与实测证据 | 结论 |
| :--- | :--- | :--- |
| **P1 注册局 RDAP** | `elenalyl.top` RDAP 状态持续为 `['client hold', 'client renew prohibited', 'client transfer prohibited', 'add period']`；NS 记录登记为 `dns1/dns2.hichina.com`；last changed 时间等于注册时间（16:04Z，注册后状态从未变更）。对照组 `liuzengyu.top` 为 `active`。 | 注册局实名认证未通过或未同步，根域不下发委派。 |
| **P2 万网权威 DNS** | 万网权威 DNS `dns1.hichina.com` 查 `kaoyan.elenalyl.top` A 记录已返回 **`43.160.227.166`**（用户在云解析的修改已成功生效）。 | 用户侧权威 DNS 解析记录已正确指向香港边缘 CVM。 |
| **P3 递归与公共 DNS (elena 视角)** | `.top` 根服务器 `a.zdnscloud.com` 查询 `elenalyl.top` NS 返回 NXDOMAIN；公共 DNS `223.5.5.5`、`8.8.8.8`、`1.1.1.1` 查询均为空；`.top` SOA minimum（负缓存 TTL）为 3600 秒。 | 因根域 NXDOMAIN，公共递归 DNS 无法解析，各级负缓存最长维持 1 小时。 |
| **P4 边缘端点直连探测** | 强制 `--resolve kaoyan.elenalyl.top:43.160.227.166`：<br>- 80 端口正常返回 `308` 永久重定向至 HTTPS；<br>- 443 端口返回 TLS alert internal error（因 CVM 上尚未签出该域名证书）。 | CVM Caddy 边缘路由规则已完全就绪，仅阻塞于 ACME 证书签发。 |
| **P5 CVM ACME 签发状态** | CVM `caddy-proxy` 容器日志显示：因 Let's Encrypt 验证时全球解析报 NXDOMAIN，已累计失败 84 次，退避重试间隔已递增至 `retrying_in 600` 秒（未拿到证书）。 | ACME 签发由于注册局 clientHold 处于退避等待状态。 |
| **P6 客户端本地解析** | M4 Clash fake-ip 依然返回 `198.18.1.94`。 | 客户端依然表现为本地 fake-ip 遇真实 NXDOMAIN 后的断流。 |

### 8.2 单一根因判定

当前**唯一且最终的硬阻塞**是注册局 `clientHold`（域名实名认证未通过或未同步到注册局），属于**纯外部阻塞**。
阿里云控制台此前提示「查询到的NS地址为空、与分配的NS不一致」亦是同一根因（根服务器查不到委派）。
服务器侧链路（香港边缘 CVM Caddyfile 配置、广州 elena 3389 回源与 User=elena 业务进程）**已 100% 准备就绪**。

### 8.3 用户唯一待办 (外部阻塞解除)

- **操作路径**：登录阿里云「域名控制台 → 域名列表 → `elenalyl.top`」；
- **具体操作**：完成域名实名认证（绑定已通过审核的信息模板）；
- **生效周期**：实名审核通过后，注册局将解除 `clientHold`（RDAP 转为 `active`）；随后需等待公共 DNS 的负缓存过期（最长约 1 小时）。

### 8.4 自动化上线守护进程 (Go-Live Watcher)

为彻底免除人工轮询、消除 CVM 退避延迟并自动恢复本地网络，已部署自动化守护进程：
- **守护脚本**：`06_elenalylGoLiveWatcher_域名解封上线守护.py`
  - 路径：`_ephemeral_blackbox/2026-10/eb_9036_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-english-web-semantic-spec-and-prd-shunt/06_elenalylGoLiveWatcher_域名解封上线守护.py`
- **LaunchAgent 配置**：`~/Library/LaunchAgents/top.elenalyl.kaoyan.watch.plist`
- **运行日志**：`~/Library/Logs/kaoyan_elenalyl_watch.log`（守护主日志）与 `~/Library/Logs/kaoyan_elenalyl_watch.launchd.log`
- **运行机制**：
  1. 每 300 秒（5 分钟）自动调度唤醒；
  2. 通过 `ssh elena` 轮询公共 DNS（`223.5.5.5` 与 `8.8.8.8`）；若未解析则记录 `WAITING` 与 RDAP 状态安全退出；
  3. 一旦公共 DNS 解析到 `43.160.227.166`，立即执行香港 CVM 容器命令：
     ```bash
     ssh cvm "docker exec caddy-proxy caddy reload --config /etc/caddy/Caddyfile --force"
     ```
     强制重置退避并触发即时证书签发；
  4. 每 20 秒高频探测 elena 端 HTTPS 访问（最多 10 分钟），得到 `200_0` 即判定上线成功；
  5. 上线成功后自动向本地 Unix Domain Socket（`/var/run/clash-verge-service/users/502/verge-mihomo.sock`）发送 `POST /cache/dns/flush` 与 `POST /cache/fakeip/flush` 清除 M4 本地 fake-ip 负缓存；
  6. 写入 `~/Library/Application Support/kaoyan_elenalyl_watch/DONE` 标记（后续周期自停），并触发 macOS 桌面横幅通知（`display notification "https://kaoyan.elenalyl.top 已上线"`）。

### 8.5 运维与清理指引

- **服务存证**：`ev:ev-0020`（`exit=0`, `verdict=met`，断言 dry-run 输出含 WAITING、LaunchAgent 处于 active、边缘 80 端口返回 308）；
- **任务卸载命令**（上线后或需手动停止时执行）：
  ```bash
  launchctl bootout gui/$(id -u)/top.elenalyl.kaoyan.watch && rm ~/Library/LaunchAgents/top.elenalyl.kaoyan.watch.plist
  ```


