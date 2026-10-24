# `kaoyan.elenalyl.top` 域名部署、证书启动与全链路访问测试报告 (Full-Chain Deployment, TLS Certificate & Access Test Report)

```yaml
[IoC_Skill_Telemetry]
Node_ID: srbg10
Agent: antigravity
LLM_Model: gemini-4-argon-high
Task_EB: eb_9036_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-english-web-semantic-spec-and-prd-shunt
Status: VERIFIED
Evidence_IDs:
  - ev:ev-0019
  - ev:ev-0020
  - ev:ev-0023
  - ev:ev-0024
Skills_Mounted:
  - completion-evidence-protocol (Skill 195)
  - anti-half-baked-reasoning
```

---

## 一、 核心测试结论速览 (Executive Summary)

> [!IMPORTANT]
> **一句话结论（物理探针实测 `ev:ev-0023`, `ev:ev-0024`）**：
> 1. **服务端与边缘网关部署状态 (`IMPLEMENTED & VERIFIED`)**：`kaoyan.elenalyl.top` 的全套前后端代码、8 表 SQLite WAL 存储 (`User=elena`, `/home/elena/kaoyan_english_hub`)、广州 `elena:3389` 回源通道以及香港边缘网关 `CVM (43.160.227.166)` 的 `Caddyfile` 站点配置（第 `1065–1078` 行）**均已 100% 部署就位并正常运行**（`CVM -> elena:3389` 实测 `HTTP 200`，耗时 `0.415s`）。
> 2. **`kaoyan.elenalyl.top` 证书与访问状态 (`PARTIAL / BLOCKED_BY_REGISTRY_CLIENT_HOLD`)**：截至 `2026-10-24T02:41:02Z`（距离域名注册约 **10 小时 37 分钟**），**`kaoyan.elenalyl.top` 仍无法签发 Let's Encrypt 证书、公网仍无法访问**。
> 3. **唯一物理阻塞点 (`[K]` 验证事实)**：上级 `.top` 注册局（ZDNS / 江苏邦宁）与阿里云万网 RDAP 显示主域名 `elenalyl.top` 仍处于 **`client hold` (`clientHold`，客户端暂停解析)** 状态，且自注册时刻 `2026-10-23T16:04:06Z` 起 **`last changed` 时间戳从未发生过任何更新**。这表明阿里云侧的**域名实名认证（信息模板关联/实名审核）尚未完成或尚未通过注册局解除 `clientHold`**，导致 `.top` 顶级根服务器 (`a.zdnscloud.com`) 对全球所有递归 DNS (`223.5.5.5` / `8.8.8.8` / `1.1.1.1`) 及 Let's Encrypt 验证节点均返回 **`NXDOMAIN`**。
> 4. **同源全功能已开通证书并可立即访问的 3 条生产 HTTPS 入口 (`VERIFIED`)**：
>    - **直连 `elena` 极速入口（推荐首选，免香港绕行，`0.145s`）**：`https://kaoyan.8.163.29.42.nip.io` （Let's Encrypt 证书已签发，`HTTP 200, SSL_VERIFY=0`）
>    - **经香港 `CVM` 同构边缘入口（与 `kaoyan.elenalyl.top` 共享完全相同的 `CVM -> elena:3389` 链路）**：`https://kaoyan.43.160.227.166.nip.io` （Let's Encrypt 证书已签发，`HTTP 200, SSL_VERIFY=0`）
>    - **存量生产域名入口**：`https://kaoyan.liuzengyu.top` （Let's Encrypt 证书已签发，`HTTP 200, SSL_VERIFY=0`）

---

## 二、 四层全链路物理探针实测矩阵 (Four-Layer Physical Probe Matrix)

测试取证脚本：[09_kaoyanSslDeployReport_域名部署与证书测试.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/09_kaoyanSslDeployReport_域名部署与证书测试.py)（入账证据：`ev:ev-0023`, `ev:ev-0024`）。

### 2.1 第一层：注册局 RDAP 与三级 DNS 解析链核验 (L1 Registry & DNS Layer)

| 检测层级 | 探测目标 / 命令 | 实测返回值 (`2026-10-24T02:41:02Z`) | 判定状态 | 根因说明 |
| :--- | :--- | :--- | :--- | :--- |
| **L1-1 `.top` 注册局 RDAP** | `https://rdap.zdnsgtld.com/top/domain/elenalyl.top` | `status: ["client hold", "client renew prohibited", "client transfer prohibited", "add period"]`<br>`last changed: 2026-10-23T16:04:06.0Z` | ❌ **BLOCKED (`clientHold`)** | 新购域名未完成实名模板过户/审核前，注册商强制锁定 `clientHold`，暂停根区 NS 委派 |
| **L1-2 阿里云注册商 RDAP** | `https://whois.aliyun.com/rdap/domain/elenalyl.top` | `status: ["client hold", ...]`<br>`last update: 2026-10-23T16:04:07Z` | ❌ **BLOCKED (`clientHold`)** | 自注册后第 1 秒起无任何状态变更事件，说明实名认证尚未在注册商侧走完解除流程 |
| **L1-3 阿里云权威 DNS** | `dig @dns1.hichina.com kaoyan.elenalyl.top A +short` (自 `elena` 发起) | `43.160.227.166` (`status: NOERROR`) | ✅ **PASS** | 您在阿里云云解析 DNS 配置的 `A` 记录已生效并指向香港 `CVM` |
| **L1-4 `.top` 顶级根权威 NS** | `dig @a.zdnscloud.com elenalyl.top NS` (自 `elena` 发起) | `status: NXDOMAIN` (`AUTHORITY: top. IN SOA a.zdnscloud.com.`) | ❌ **NXDOMAIN** | 因 `clientHold` 未解除，`.top` 顶级根区拒绝下发 `dns1/dns2.hichina.com` 委派记录 |
| **L1-5 全球公共递归 DNS** | `dig @223.5.5.5` / `@8.8.8.8` / `@1.1.1.1 kaoyan.elenalyl.top A` | 全部返回 `status: NXDOMAIN` | ❌ **NXDOMAIN** | 全球递归 DNS 从 `.top` 根服务器直接收到 `NXDOMAIN`，无法触达 `dns1.hichina.com` |

---

### 2.2 第二层：香港边缘网关 (`CVM 43.160.227.166`) 与 Let's Encrypt 证书签发核验 (L2 Edge & ACME Layer)

| 检测项 | 物理探针命令 | 实测输出摘要 | 判定状态 |
| :--- | :--- | :--- | :--- |
| **`CVM` Caddyfile 站点块部署** | `grep -n -A 15 'kaoyan.elenalyl.top {' /opt/ihg_hotel/10_deploy/Caddyfile` | 第 `1065–1078` 行：`kaoyan.elenalyl.top` 已配置 `reverse_proxy 8.163.29.42:3389` + `header_up Host 127.0.0.1` | ✅ **DEPLOYED (`ev:ev-0019`)** |
| **`CVM` HTTP `:80` 路由探针** | `curl -sI --resolve kaoyan.elenalyl.top:80:127.0.0.1 http://kaoyan.elenalyl.top/` | `HTTP/1.1 308 Permanent Redirect` -> `Location: https://kaoyan.elenalyl.top/` | ✅ **PASS** |
| **Let's Encrypt ACME 证书签发日志** | `docker logs caddy-proxy 2>&1 \| grep elenalyl` | `attempt: 21`, `retrying_in: 7200`, `error: HTTP 400 urn:ietf:params:acme:error:dns - DNS problem: NXDOMAIN looking up A for kaoyan.elenalyl.top` | ⏳ **WAITING_ON_DNS** |
| **`CVM` HTTPS `:443` 握手探针** | `curl -vI --resolve kaoyan.elenalyl.top:443:127.0.0.1 https://kaoyan.elenalyl.top/` | `TLSv1.3 (IN), TLS alert, internal error (592)`（因 `NXDOMAIN` 导致证书尚未签发落盘） | ❌ **NO_CERT_YET** |

> [!NOTE]
> **为什么不能启动 `kaoyan.elenalyl.top` 的受信任 HTTPS 证书？**
> Let's Encrypt 在签发证书时（无论 `HTTP-01`、`TLS-ALPN-01` 还是 `DNS-01`），其美国/欧洲多点验证服务器（Multi-Perspective Validation）第一步必须从互联网根域名服务器（`.` -> `.top` 根 `a.zdnscloud.com`）递归解析 `kaoyan.elenalyl.top`。只要 `.top` 注册局未解除 `elenalyl.top` 的 `clientHold` 状态，Let's Encrypt 查询 `.top` 根服务器就会直接收到 `NXDOMAIN`，从而立即拒绝签发（`urn:ietf:params:acme:error:dns`）。

---

### 2.3 第三层：广州 `elena` (`8.163.29.42`) 源站服务、回源链路与冷热存储核验 (L3 Origin & Backhaul Layer)

| 检测项 | 实测指标 (`ev:ev-0023`, `ev:ev-0024`) | 判定状态 |
| :--- | :--- | :--- |
| **`elena` 进程权限与服务状态** | `kaoyan-english-hub.service`: **`active`** (`User=elena`, PID `21374`, `/usr/bin/python3 /home/elena/kaoyan_english_hub/kaoyan_hub_server.py`)<br>`caddy.service`: **`active`** | ✅ **PASS** |
| **`CVM -> elena:3389` 跨地域回源探针** | `curl -H "Host: 127.0.0.1" http://8.163.29.42:3389/api/health` -> **`HTTP_CODE=200 TIME=0.415s`** | ✅ **PASS** |
| **SQLite WAL 8 表热库状态** | `/home/elena/kaoyan_storage/hot_db/kaoyan_hub.sqlite3` (`92KB`, owner `elena:elena`, 8 张核心表完整在线：`annotation_spans`, `essay_corpus_snippets`, `exam_passages`, `schema_migrations`, `syllabus_5500_lexicon`, `sys_users`, `user_progress_anchors`, `user_vocab_ledger`) | ✅ **PASS** |
| **M4 自动解封上线守护进程** | `launchctl list \| grep top.elenalyl.kaoyan.watch` -> **`active (exit=0)`**，每 5 分钟自动巡检 RDAP 与公共 DNS；一旦 `clientHold` 解除，自动触发 `CVM` Caddy 强制签发证书并刷新 M4 缓存 | ✅ **ACTIVE (`ev:ev-0020`)** |

---

### 2.4 第四层：同源已上线 HTTPS 域名与 P1/P2/P3 全量业务接口实测 (L4 Live Endpoints & Functional Matrix)

虽然 `kaoyan.elenalyl.top` 因域名注册局 `clientHold` 暂时无法签发证书，但部署在同一套 `elena` 源站与香港 `CVM` 边缘网关上的 **3 个兄弟域名均已完成 Let's Encrypt 证书签发并通过 P1/P2/P3 全量测试**：

#### A. 四大入口 HTTPS 证书与连通性对比表

| 域名入口 | 路由拓扑 | HTTP 状态码 | TLS 证书校验 (`SSL_VERIFY`) | 端到端总耗时 (`TIME`) | 可用性结论 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`https://kaoyan.8.163.29.42.nip.io`** | 浏览器 $\rightarrow$ 广州 `elena:443` $\rightarrow$ `:60231` | **`200 OK`** | **`0` (Let's Encrypt 有效)** | **`0.145s` (最快)** | ✅ **全网直连可用（推荐首选）** |
| **`https://kaoyan.43.160.227.166.nip.io`** | 浏览器 $\rightarrow$ 香港 `CVM:443` $\rightarrow$ 广州 `elena:3389` $\rightarrow$ `:60231` | **`200 OK`** | **`0` (Let's Encrypt 有效)** | **`3.240s`** | ✅ **全网可用（与 `kaoyan.elenalyl.top` 同构链路）** |
| **`https://kaoyan.liuzengyu.top`** | 浏览器 $\rightarrow$ 香港 `CVM:443` $\rightarrow$ 广州 `elena:3389` $\rightarrow$ `:60231` | **`200 OK`** | **`0` (Let's Encrypt 有效)** | **`3.013s`** | ✅ **全网可用** |
| **`https://kaoyan.elenalyl.top`** | 浏览器 $\rightarrow$ 香港 `CVM:443` $\rightarrow$ 广州 `elena:3389` $\rightarrow$ `:60231` | `000` (TLS 终止) | `1` (尚无证书) | `5.005s` | ⏳ **待阿里云实名解除 `clientHold` 后自动开通** |

#### B. 考研英语工作台 (`elena` 实例) 核心业务路由实测 (`ev:ev-0024`)

| 请求方法与路由 | 用途说明 | 实测响应指标 (`https://kaoyan.8.163.29.42.nip.io`) | 判定状态 |
| :--- | :--- | :--- | :--- |
| `GET /` | 考研英语工作台 v2.4 三模态双视口 SPA 主界面 | `HTTP=200 SSL=0 SIZE=67777 bytes TIME=0.263s` | ✅ **PASS** |
| `GET /api/health` | 容器/服务健康探针与 SQLite WAL 8 表结构自检 | `HTTP=200 SSL=0 SIZE=345 bytes TIME=0.163s` | ✅ **PASS** |
| `GET /api/state` | 初始化全量状态拉取（真题篇章、大纲词汇、作文语料、锚点进度） | `HTTP=200 SSL=0 SIZE=298 bytes TIME=0.185s` | ✅ **PASS** |
| `POST /api/progress/anchor` | 阅读位置锚点持久化（RBAC 未登录态拦截校验） | `HTTP=401 SSL=0 SIZE=133 bytes TIME=0.138s` (符合零信任鉴权预期) | ✅ **PASS** |
| `POST /api/vocab/lookup` | 词汇查词与生词本入账（RBAC 未登录态拦截校验） | `HTTP=401 SSL=0 SIZE=133 bytes TIME=0.136s` (符合零信任鉴权预期) | ✅ **PASS** |

---

## 三、 下一步操作指引：如何彻底解除 `elenalyl.top` 的 `clientHold`

1. **检查阿里云域名控制台实名状态**：
   - 登录 [阿里云域名控制台 - 域名列表](https://dc.console.aliyun.com/next/index#/domain-list/all)。
   - 查看 `elenalyl.top` 的**「实名认证状态」**：
     - 若显示**「未实名认证」**，请点击右侧**「实名认证」**并直接选择您账号下**已认证通过的信息模板**提交过户（无需重新上传身份证，绑定已有实名模板最快数十分钟即可上报 `.top` 注册局解除 `clientHold`）。
     - 若显示**「实名审核中」**，则等待注册局（ZDNS）审核回执即可。
2. **全自动证书签发与零人工介入上线**：
   - 您本机 `M4` 上的守护服务 `top.elenalyl.kaoyan.watch`（脚本：[06_elenalylGoLiveWatcher_域名解封上线守护.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/06_elenalylGoLiveWatcher_域名解封上线守护.py)）正以每 5 分钟一次的频率后台巡检。
   - 一旦 `elenalyl.top` 的 `clientHold` 解除，守护进程将自动通知香港 `CVM` 执行 `caddy reload --force` 立即完成 Let's Encrypt 证书签发，并自动清空 `M4` Clash Verge 缓存，无需任何手动重启。
