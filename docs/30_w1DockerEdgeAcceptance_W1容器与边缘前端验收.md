# W1容器与边缘前端八层架构及多阶段验收总纲 / W1 Docker & ECS Edge L0–L7 Acceptance Specification (#30)
> [IoC_Skill_Telemetry] Status: VERIFIED; Author/Exec: Codex/OpenAI + Antigravity/Qwen3.8-Max; Evidence: ev:ev-0029, ev:ev-0030, ev:ev-0032, ev:ev-0034, ev:ev-0035, ev:ev-0040

> **Status**: `IMPLEMENTED` & `VERIFIED` (`eb_20261024#ev-0029..0040` · `eb_9041#ev-0001..0022` · `46/46 Public HTTPS HA Assertions PASS` · `22/22 Issues Closed`)
> **受治落盘路径**: [30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.md)
> **四模态伴生编译器**: [30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.py)
> **0-Token 前置限幅外专 v2.0**: [kaoyan_w1_docker_edge_shunt_engine.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_w1_docker_edge_shunt_engine.py)
> **关联深度报告与 ADR**: [03_phase_test_report.md](file:///Users/liuzengyu/treeworker/workers/srbg10/_ephemeral_blackbox/2026-10/eb_20261024_srbg10_H_codex_gpt-6_kaoyan-w1-docker-edge-audit/03_phase_test_report.md) · [05_deployment_acceptance.md](file:///Users/liuzengyu/treeworker/workers/srbg10/_ephemeral_blackbox/2026-10/eb_20261024_srbg10_H_codex_gpt-6_kaoyan-w1-docker-edge-audit/05_deployment_acceptance.md) · [ADR-0715](file:///Users/liuzengyu/treeworker/workers/srbg10/.adr/701-800/711-720/adr_0715_w1DockerEdgePlacement_边缘前端与容器主库分离/adr_0715_w1DockerEdgePlacement_边缘前端与容器主库分离.md)

---

## 一、 L0–L7 底层八层架构与 4A 架构全景矩阵 (8-Layer Stack & 4A Architecture Matrix)

| 层级 | 架构平面 (`4A`) | 底层内核/虚拟化/协议与物理载体 (`[K]` 实证事实) | 关键工程不变量与安全围栏 | 实证物证 (`ev:`) |
| :---: | :--- | :--- | :--- | :--- |
| **`L0`** | **物理与异构硬件基板层** (`TA`) | `Elena ECS` (`2C / 1735 MiB RAM / 0 Swap`)；`W1` (`i7-14700 20C / 32 GB DDR5 / Win11`)；`HP` (`i9 16C / 128 GB / Ubuntu x86_64`)；`S1` (`M5 Max 18C / 64 GB / macOS arm64`)；`T2` (`18.2 TB Btrfs 冷备目标`) | 节点地址由 `node_ip_resolver.py` 动态解析，严禁源码硬编码局域网 IP；`remote.py` 自动预热缓存并对 `ControlMaster` 闪断执行 3 次退避重试 | `ev:ev-0003`, `ev:ev-0027`, `ev:ev-0040` |
| **`L1`** | **宿主内核、WSL2 与 VFS 存储层** (`TA`) | `W1` Windows 计划任务 `KaoyanDockerWSL` (`S4U` 最高权限, `RestartCount=99`) 自启动 `WSL2 Ubuntu-26.04` (`Linux 6.6.87.2-microsoft-standard-WSL2`) 与 `systemd` 双守护服务 | 生产 SQLite WAL 热卷挂载于 WSL2 原生 `/dev/sdd` (`ext4` VHDX) `/srv/kaoyan-docker/{worker,gateway}`，严禁跨 `DrvFs/9P` (`/mnt/c`) 挂载规避 POSIX 文件锁失效 | `ev:ev-0009`, `ev:ev-0034`, `ev:ev-0040` |
| **`L2`** | **OCI 容器安全加固与 Cgroup v2 层** (`TA/AA`) | `Docker Engine 29.1.3` 运行 `kaoyan-cluster:56a8353092a2`：`kaoyan-w1-gateway` (`512m` 上限，实测 `24.44 MiB`) + `kaoyan-w1-worker` (`256m` 上限，实测 `19.47 MiB`) | `read_only: true` 只读根文件系统、`user: "1000:1000"`、`cap_drop: [ALL]`、`no-new-privileges: true`、`pids_limit: 128`、缺卷 Fail-Closed 拒启动 | `ev:ev-0015`, `ev:ev-0030`, `ev:ev-0040` |
| **`L3`** | **18 表 × 146 字段存储与冷备金库层** (`DA`) | `SQLite 3.46.1` (`W1/HP`) 与 `3.54.0` (`S1`)；`PRAGMA journal_mode=WAL`、`synchronous=FULL`、`foreign_keys=ON`；全库 **18 张表、146 个字段**零外键违例 | 退役历史库 (`legacy-kaoyan.sqlite3`, `legacy-kaoyan.pgbackup`) 与当前生产冷备 (`production-cold-20261024.sqlite3`) 在 **`W1 + HP + S1` 三主机冷备金库** 100% SHA-256 对齐 + `T2` 离线队列 | `ev:ev-0014`, `ev:ev-0034`, `ev:ev-0035` |
| **`L4`** | **Epoch 围栏状态机与两阶段复制协议层** (`TA/DA`) | 单一持久权威协调器 + 单调递增 `epoch` (`production.fence.json` 原子 `os.replace+fsync`) + `version` (`ha_cluster_meta`) + `pending` 两阶段 (`execute -> replicate`) 恢复日志 | 稳态采用 **`1.8 KB` `meta_snap` 元数据先验对账**（替代 `410 KB` 全库 Base64，网络载荷降低 **`99.56%`**）；`GET/HEAD` 只读快路径免除二次同步；HP `epoch+1` 热备协调器 `15.684s` 自动接管 | `ev:ev-0029`, `ev:ev-0030`, `ev:ev-0032`, `ev:ev-0035` |
| **`L5`** | **最小权限回环 SSH 隧道网格层** (`TA`) | `ECS Caddy -> HP kaoyan-w1-gateway-relay -> W1:28331`；`W1 kaoyan-replica-tunnels -> HP:18104 & S1:18104`；`/_cluster/control` 强制 `hmac.compare_digest` Bearer 鉴权 | `ed25519` 专用密钥强制 `restrict,port-forwarding,permitopen="127.0.0.1:<port>"`；拦截多重 `Content-Length` / `Transfer-Encoding` 走私 | `ev:ev-0002`, `ev:ev-0015`, `ev:ev-0040` |
| **`L6`** | **ECS 边缘白名单静态分发与应用层** (`BA/AA`) | `Elena ECS` Caddy 直接托管 `/srv/kaoyan-edge/releases/384734286736` 下 6 个白名单静态资产 (`153,169 B`)，注入 `X-Kaoyan-Frontend: ecs-static` | `MAX_RELEASES=5` 自动 LRU 淘汰（总占用 `< 16 MiB`）；`*.py` 源码路径硬拦截或 `302` 回跳 `/`；`/api/*` 强制 `Cache-Control: no-store` | `ev:ev-0008`, `ev:ev-0023`, `ev:ev-0034`, `ev:ev-0040` |
| **`L7`** | **前置限幅外专、物证链与治理层** (`4A`) | `kaoyan_w1_docker_edge_shunt_engine.py` (`v2.0`, 脱水率 `98.04%`) + `--mode live-l0-l7-probe` 跨 4 节点实时巡检 + `srbg10` 单写租约溯源清障 | 所有完成声明绑定 `ev:` 防篡改哈希链物证（`[C39]`）；衍生二进制 `.svg/.png/.pptx` 本地落盘不进 Git（`gate_0292`） | `ev:ev-0029`, `ev:ev-0035`, `ev:ev-0040` |

---

## 二、 22 项底层故障与架构瓶颈根因穿透矩阵 (`B01–B12` & `D01–D10`)

| 编号 | 层级 | 故障/瓶颈现象 (`[现象]`) | 底层内核/协议/治理根因 (`[根因]`) | 根治方案与验证物证 (`[治理]`) |
| :---: | :---: | :--- | :--- | :--- |
| **`B01–B03`** | `L0–L3` | `runtime_audit` 键名报错、缺卷空库自举风险、W1 拉取基础镜像超时 | `inventory()` 返回 `rows` 而非 `count`；旧启动器缺卷自动建空表；跨境 Docker Hub 超时 | 修正字段契约；`kaoyan_cluster_launch.py` 强制 `require_existing_files` Fail-Closed；复用本地已校验镜像缓存 (`ev:ev-0003`, `ev:ev-0004`, `ev:ev-0010`) |
| **`B04–B08`** | `L2/L5/L6` | Caddy 未知路径空白 200、沙盒 TLS 偶发重置、`compose.w1.yml` `tmpfs` 报错、PowerShell 剥离 `permitopen` 双引号、Canary 占位符误伤 | Caddy `redir` 参数顺序歧义；YAML 行内数组逗号拆裂；PowerShell 原生 `-c` 吞掉内嵌双引号；`IMAGE` 子串碰撞 `KAOYAN_IMAGE` | 显式 `@spa` matcher；`tmpfs` 字符串整体加引号；`remote.py` 全量采用 Base64 编码载荷；独立唯一占位符 (`ev:ev-0008`, `ev:ev-0015`, `ev:ev-0016`) |
| **`B09–B12`** | `L2/L3/L5` | 归档拷贝瞬态 `-wal` 报错、CLI 缺 `tables` 字段、容器重启 `Health=starting` 误判、单测连续重载报 `Stale epoch` | `journal_mode=DELETE` 自动清理 `-wal`；CLI 默认省略大表哈希；Docker `start_period` 窗口；`kaoyan_runtime` 与 `kaoyan_repository` 重载顺序倒置 | 显式关闭连接并校验稳定文件；新增 `--include-tables`；按 Healthcheck 预算轮询 `starting`；修正模块重载顺序 (`ev:ev-0018`, `ev:ev-0025`, `ev:ev-0029`) |
| **`D01`** | `L4` | 稳态请求公网延迟 `3.6s–10.5s`，跨节点在线切主耗时 `6.8s` | 每次请求无条件向 3 节点广播 `410 KB` Base64 全库 (`1.23 MB`)，`Worker.install` 重复执行 2 遍 18 表扫描，只读 `GET` 触发冗余备份与二次同步 | 实装**两阶段元数据优先同步 (`meta_snap` `1.8 KB`，降载 `99.56%`)** + 单遍表扫描 + `GET/HEAD` 只读快路径；切主提速 **`45.6×` (`149.55 ms`)** (`ev:ev-0030`, `ev:ev-0035`) |
| **`D02–D03`** | `L0/L3/L5` | 并发 SSH 偶发 `port 65535` 闪断；冷备仅存 W1 单节点且 `T2` 跨网段离线 | `ControlMaster` 多路复用瞬时竞争；ECS 旧定时任务停用后未建跨机多副本金库 | `remote.py` 集成 3 次指数退避重试 + 自动降级 `ControlMaster=no`；建立 **`W1 + HP + S1` 三主机冷备金库** + `T2` 离线同步队列 (`ev:ev-0027`, `ev:ev-0034`) |
| **`D04–D06`** | `L1/L4/L6` | 单协调器停机缺乏自动围栏接管演练；WSL2 未测整栈冷重启；ECS 静态版本目录无限累积 | 仅文档描述手工恢复；仅测单容器 `docker restart`；`deploy_edge.py` 无历史版本淘汰 | 实装 `kaoyan_coordinator_failover.py` 完成 `W1 -> HP (epoch=23, 15.68s) -> W1 (epoch=24, 169.81ms)` 演练；实测 WSL2 双服务冷重启；ECS 启用 `MAX_RELEASES=5` LRU (`ev:ev-0032`, `ev:ev-0034`) |
| **`D07–D08`** | `L5/L7` | 缺乏 0-Token 前置限幅外专；初版 03/05/30 报告简略且缺四模态资产 | 多机原始遥测达 `186.4 KB`；初版仅落盘简短摘要 | 实装 `kaoyan_w1_docker_edge_shunt_engine.py`（压缩率 `98.04%`）；全面扩写 `03`、`05` 与 `30` 号报告 (`ev:ev-0029`, `ev:ev-0035`) |
| **`D09`** | `L7` | `srbg10` 单写租约被僵尸会话 `e52c7517` 霸占，阻断 Phase 6 最终收口 | Codex 桌面线程 `01a16f50` 派生的无头 `agy` 只读复核子进程触发会话钩子抢占 `task.json`，退出后未释放且遗留 22 个脏文件 | 实装 `srbg10_lease_forensics_and_unblock_shunt.py` 溯源死进程，清零 22 个脏文件并完成 `VERIFIED` 收口 (`d4e3658239ff`) |
| **`D10`** | `L0–L7` | 缺乏一键式 `L0–L7` 跨 4 节点实时巡检算子与 30 号四模态编译器 | 前期 shunt 仅含静态与本地单测模式，30 号报告仅 11 行豁免态 | 升级 `kaoyan_w1_docker_edge_shunt_engine.py` 新增 `--mode live-l0-l7-probe` (`ev:ev-0040`, `eb_9041#ev-0022`)，并实装 `30_w1DockerEdgeAcceptance_W1容器与边缘前端验收.py` |

---

## 三、 优化前后关键性能与高可用量化对比 (Before vs. After Quantitative Benchmarks)

| 关键工程指标 | 初版切入基线 (`ev:ev-0019` / `ev:ev-0021`) | 深度架构优化后实测 (`ev:ev-0030` / `ev:ev-0032` / `ev:ev-0035` / `ev:ev-0040`) | 优化幅度 |
| :--- | :---: | :---: | :---: |
| **稳态单次请求跨机同步载荷** | `3 × 410 KB = 1,230 KB` | **`3 × 1.8 KB = 5.4 KB`** (`meta_snap`) | **降低 `99.56%`** |
| **公网 HTTPS `GET /api/health` 延迟** | `3,807.99 ms` | **`834.05 ms`** | **提速 `4.57×`** |
| **公网 HTTPS `GET /api/passages` 延迟** | `3,639.32 – 7,025.04 ms` | **`689.01 ms`** | **提速 `5.28× ~ 10.2×`** |
| **公网幂等重放 (`idempotent_replay`) 延迟** | `6,825.08 – 8,348.27 ms` | **`177.01 – 249.62 ms`** | **提速 `30.8× ~ 38.5×`** |
| **跨三节点在线切主耗时 (`switch_ms`)** | `S1: 6,822ms / HP: 6,737ms / W1: 6,835ms` | **`S1: 149.55ms / HP: 159.67ms / W1: 238.40ms`** | **提速 `28.7× ~ 45.6×`** |
| **46 项公网全量高可用验收总耗时** | `132.006 s` | **`77.302 s`** (含 30s 真实断链故障窗口) | **缩短 `41.4%`** |
| **协调器停机容灾接管 (`W1 -> HP -> W1`)** | 无自动化演练 | **`15.684 s` 接管 (`epoch=23`) / `169.81 ms` 回切 (`epoch=24`)** | **消除单点盲区** |
| **L0–L7 跨 4 节点实时全栈巡检耗时** | 手工分步取证 | **`6,663.84 ms` 一键全绿 (`live-l0-l7-probe`)** | **100% 自动化** |

---

## 四、 八阶段 (`P0–P7`) 全链路实施与验收闭环总表 (8-Phase Acceptance Summary)

| 阶段 | 阶段名称与核心交付 | 验收结果与物证 (`eb_20261024` / `eb_9041`) |
| :---: | :--- | :--- |
| **`P0`** | 四节点并发实机取证、18 表 146 字段基线与 0-Token 前置限幅外专构建 | **VERIFIED** (`ev:ev-0003`, `ev:ev-0014`, `ev:ev-0027` / `eb_9041#ev-0001`) |
| **`P1`** | `L0–L7` + `4A` 架构设计、生产卷缺失 Fail-Closed 守卫与 `ADR-0715` 契约落盘 | **VERIFIED** (`ev:ev-0004`, `ev:ev-0029` / `eb_9041#ev-0003`) |
| **`P2`** | 两阶段元数据优先同步、`GET/HEAD` 只读快路径与 37 项真容器/跨机回归套件热升级 | **VERIFIED** (`ev:ev-0010`, `ev:ev-0015`, `ev:ev-0029`, `ev:ev-0030` / `eb_9041#ev-0004`) |
| **`P3`** | W1 WSL2 Docker 默认主库切入与 HP `epoch+1` 备用协调器容灾接管及回切演练 | **VERIFIED** (`ev:ev-0016`, `ev:ev-0032` / `eb_9041#ev-0005`) |
| **`P4`** | ECS 5 版本静态 LRU 限幅、`W1+HP+S1` 三主机冷备金库 + `T2` 队列、WSL2 全栈冷重启 | **VERIFIED** (`ev:ev-0008`, `ev:ev-0018`, `ev:ev-0034` / `eb_9041#ev-0006`) |
| **`P5`** | 公网 HTTPS (`https://kaoyan-elena.duckdns.org`) 46 项高可用断言与切主 45.6 倍提速终验 | **VERIFIED** (`ev:ev-0019`, `ev:ev-0025`, `ev:ev-0035` / `eb_9041#ev-0007`) |
| **`P6`** | `srbg10` 僵尸单写租约溯源清障 (`D09`)、22 个历史脏文件清零与唯一 `origin` 原子推送 | **VERIFIED** (`ev:ev-0026`, `ev:ev-0036` / `eb_9041#ev-0012..0021`) |
| **`P7`** | `L0–L7` 跨四节点实时巡检探针 (`--mode live-l0-l7-probe`) 与 30 号四模态交付物编译收口 | **VERIFIED** (`ev:ev-0040` / `eb_9041#ev-0022`) |

---

[IoC_Revision_v1] Status: VERIFIED; Agent: TailClosed; Evidence: ev:ev-0029, ev:ev-0030, ev:ev-0032, ev:ev-0034, ev:ev-0035, ev:ev-0040, eb_9041#ev-0022; 完成 L0–L7 与 4A 深度架构全篇扩写、22 项问题闭环、P0–P7 八阶段真机验收及 30 号四模态 (.md/.py/.svg/.png/.pptx/.html) 同源编译。
