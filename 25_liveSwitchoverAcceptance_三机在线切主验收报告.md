# 在线切主与 W1 库表部署测试验收报告 / Live switchover acceptance
> [IoC_Skill_Telemetry] Status: VERIFIED（下述验收范围） · Author/Exec: Codex/OpenAI · 2026-10-24 · srbg10
> 生产入口：[研词真源](https://kaoyan.liuzengyu.top)；证据目录：`_ephemeral_blackbox/2026-10/eb_20261020_srbg10_H_codex_gpt-6_kaoyan-live-switchover-windows`。
## 交付结论 / Outcome
[K] W1 已部署 Windows 原生常驻后端和生产库，非 WSL、非本机贴 OS 标签；S1 按用户授权替代 M1。
[K] 公网写入统一经 HP 协调器，HP/W1/S1 均可作为实际 SQL 执行主节点；生产切主和历史数据核验通过 ev:ev-0023、ev:ev-0029。
[K] 生产完整保存旧主 16 张表，再增加 2 张协议表，共 18 张；14 张业务表、旧扩展表、账号密码及全部历史行均保留。
[K] 在 W1 原生部署的验收库中真实删除已填充的 user_vocab_ledger 后，保留损坏库并恢复完整内容，三机逐表摘要一致：ev:ev-0021；生产库未做破坏性丢表注入。
## 实机与常驻部署 / Native deployment
| 节点 | 实际 OS / 架构 | Python / SQLite | 常驻机制 | 生产数据位置 |
|---|---|---|---|---|
| W1 | Windows / AMD64 | 3.13.9 / 3.50.4 | SYSTEM 启动任务 KaoyanLiveWorker | C:\Users\lenovo3\kaoyan_live_20261024\data\production.sqlite3 |
| HP | Linux / x86_64 | 3.14.4 / 3.46.1 | systemd worker/gateway/tunnels | /home/hp/kaoyan_live_20261024/data/production.sqlite3 |
| S1 | macOS / arm64 | 3.9.6 / 3.54.0 | 用户 launchd KeepAlive | /Users/baigong/kaoyan_live_20261024/data/production.sqlite3 |
S1 LaunchAgent 随用户会话启动；注销后少一个副本，HP/W1 仍可构成两个确认副本。初次三机身份与表部署：ev:ev-0007。
## 纸面与实际差异 / Corrected claims
| 旧说法或现状 | 本轮实测与修复 |
|---|---|
| 快照迁移等于在线 HA、18ms 瞬时切主 | 已实现在线写入与 epoch 切主；实际为秒级，撤回旧毫秒承诺 |
| HTTP 200、行数相等就算同步 | 校验 SQLite 完整性、全表值摘要、完整 DDL 摘要、版本和历史行子集 |
| 业务写入后另写审计/幂等记录 | 整个请求同一事务；失败回滚，回执随快照复制 |
| 表数据相同即可跳过恢复 | 修复索引/触发器/视图结构变更被遗漏；先红后绿 ev:ev-0003 → ev:ev-0005 |
| 已登录即可按任意 span_id 写入 | 修复批注、升格、作文的归属检查；ev:ev-0008 → ev:ev-0010、ev:ev-0021 |
| 非法数值是普通单次报错 | 修复 pending 队列被坏输入堵死；ev:ev-0012 → ev:ev-0013 |
| 页面默认 PG18 在线、100% 同步 | 改为未知初态及真实副本/表数；ev:ev-0024、ev:ev-0025 |
| Windows 与 Linux 的 HTTP 代理行为一致 | 内部 RPC 显式直连；污染代理回归 ev:ev-0030 → ev:ev-0031 |
| HP 旧库就是生产真源 | 以 elena 实际进程环境中的 hot_db 为真源；默认 db_volume 是闲置旧库，ev:ev-0020 |
## 测试证据 / Evidence
- 既有缺表/迁移 13 项回归 + 在线协议回归，均在三机原生解释器运行；最终代理隔离版证据见末尾追加。
- 三机在线联调 53 条断言：并发写、真实切主、密码轮换、RBAC、非法输入、单节点掉线、双节点不可用、主节点退出、W1 丢表恢复、协调器重启：ev:ev-0021。
- 公网生产验收 42 条断言：HTTPS 写入、W1/S1/HP 切主、同键重放、全部历史行保留、实际跨机隧道中断与追平：ev:ev-0029。
- 已确认写入在已测试的故障/切换路径中丢失数为 0；重复词频未增加。业务 2xx 只有在协调器持久化且至少两个工作节点确认后返回。
- HP/S1 公网 TLS 与页面内容：ev:ev-0027、ev:ev-0028；W1 显式直连 TLS：ev:ev-0032，未关闭证书验证。
- W1 默认系统代理仍指向拒接的本机代理；仅本业务内部 RPC 和验收探针隔离代理，不宣称其全局浏览器代理已修复。
- 前端 POST 自动重试最多三次，保持同一幂等键和请求体；耗尽后显示“保存尚未确认”，不保存密码到重试队列：ev:ev-0024。
## 测量结果 / Measurements
首次旧生产系统迁入冻结写入 **24.79 秒**，不是零停机；迁入后的节点切主由入口排队并保护在途事务。
首轮公网切主：HP→W1 **2765.19ms**、W1→S1 **2550.78ms**、S1→HP **2705.13ms**；该轮请求中位数 **2938.75ms**，最大 **3650.84ms**。
四并发真机压力轮请求最大 **19502.72ms**（含故障等待与排队）；53 条断言仍全部满足。此实现适合当前低流量库，不能宣称高吞吐或瞬时迁移。
最新隧道中断轮原始耗时记录保存在 production_acceptance.json；不混用两轮测量值。
## 操作与回滚 / Operations
本地一条命令（无需复制凭据）：`python3 kaoyan_cluster_admin.py --ssh hp status`；切换用 `switch W1`、`switch S1` 或 `switch HP`。
当前生产主节点保持 HP。协调器与工作节点配置均在各机 kaoyan_live_20261024 内，令牌/SSH 私钥未进入 Git。
初始主库备份：elena 的 kaoyan_english_hub/db_backups/live_20261024_final.sqlite3；HP 旧备用库单独保留同名备份和原停止容器。
Caddy 原配置在原目录的 Caddyfile.live-before-20261024；旧 elena 应用停用，旧业务入口转发到同一正式入口。
切入后回滚必须先冻结新入口，将 production_coordinator.sqlite3 中权威 snapshot 回灌旧库并验证；严禁直接启动旧快照回退已确认数据。
## 验收边界 / Limits
单 HP 协调器是明确的可用性依赖；不是 Raft 共识、自动选举或 PG18 复制。少于两个可用工作节点会返回 503，恢复后同键重试。
范围内已复现缺陷均有修复与回归；“通过本轮验收”不等于所有未来输入、容量、断电、磁盘损坏与网络组合永远无 bug。
本轮未做物理断电、长时间压力、32MiB 以上快照容量与协调器整盘丢失实验；未宣称通过。
elenalyl.top 的注册/DNS/证书问题独立存在；当前交付入口为上方已验证的正式域名。
## 规格、修复和来源 / Traceability
规格：19_liveSwitchoverPrd；修复轮次：20、21、22、23、26、27；生产切入裁决：24；架构决策 ADR-0713。
使用 blade-router、engineering-workflows、test-copilot-buddy；实际执行者为 Codex，未伪报异源外专调用。
[SQLite 单写事务](https://www.sqlite.org/lang_transaction.html) 与 [一致备份](https://www.sqlite.org/backup.html)支撑事务/快照设计；复制确认协议由本项目实现。
边缘配置先验证再平滑 reload，参照 [Caddy CLI](https://caddyserver.com/docs/command-line#caddy-reload)。


## [IoC_Revision_vLiveFinal]
Status: VERIFIED；最终版本三机各 13 项库表 + 10 项协议测试：S1 ev:ev-0034、HP ev:ev-0035、W1 ev:ev-0036；最终公网断链/切主/历史行验收 ev:ev-0038。
最终发布源码与 SQL 文件逐一 SHA-256 核验，HP/W1/S1 全部与交付源文件一致：ev:ev-0039；当时 39 条证据的哈希链完整，失败记录保留用于追溯。随后交付已推送 HP origin 并校验远端对象：ev:ev-0040。
最终公网复测 ev:ev-0038：HP→W1 3094.84ms、W1→S1 3176.41ms、S1→HP 3020.53ms；最终主节点 HP，任期 12。该轮数据对应 production_acceptance.json。
仓库提交门禁同时披露存量治理基线：9 PASS / 3 WARN / 1 BLOCK（既有豁免），未改写基线；详见本 EB scratchpad/commit-*.log。

## English acceptance summary
W1 runs a native Windows service with the real production database; HP runs Linux and S1 runs macOS as the authorized replacement for M1. Each production database has 18 tables: all 16 source tables plus two protocol tables.
The final native suites passed 23 tests on each host (ev:ev-0034–0036). The public HTTPS suite passed 42 assertions, including writes on each selected primary, link failure/recovery and preservation of every historical row (ev:ev-0038). All deployed source hashes match the delivered release (ev:ev-0039).
Each confirmed write is an atomic request transaction with replicated receipts and at least two worker acknowledgements. W1 missing-table recovery was exercised on its native deployed canary database (ev:ev-0021); production data was preserved during the cutover.
The initial migration paused writes for 24.79 seconds. The final primary switches took 3.095, 3.176 and 3.021 seconds. The HP coordinator remains a single availability dependency; physical power loss, coordinator disk loss and large-volume sustained workloads were not tested.
All reproduced defects in the executed scope were repaired and retested. This is a scoped acceptance result, not a guarantee against every future bug. W1's unrelated global proxy setting and the legacy elenalyl.top domain remain separate operational issues.
