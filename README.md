# 研词真源 / Kaoyan English Hub
> [IoC_Skill_Telemetry] Status: VERIFIED（本轮范围） · Codex/OpenAI · 2026-10-24 · ev:ev-0038
正式入口：[研词真源](https://kaoyan.liuzengyu.top)。当前生产主节点 HP，W1 Windows / S1 macOS 可在线切为执行主。

完整交付见 [在线验收报告](25_liveSwitchoverAcceptance_三机在线切主验收报告.md)；规格见 [语义单与 PRD](19_liveSwitchoverPrd_在线切主语义单与实施方案.md)。
本次已在真实 W1 部署原生常驻后端与生产数据库，并实测丢表恢复、跨机切主、断链恢复、完整数据保留。

生产架构：固定 HTTPS 入口 → HP 持久协调器 → HP/W1/S1 原生 SQLite 工作节点；成功响应要求至少两个节点确认。
完整生产库共 18 表：14 张 V005 业务表、2 张原有扩展表、2 张事务/回执协议表。
代码真源在本目录 kaoyan_*.py；backend/kaoyan_hub_server.py 仅兼容启动，旧复制模块不是发布真源。
生产进程使用 kaoyan_cluster_launch.py 与各机私有配置；禁止启动旧服务器直写 production.sqlite3。

运维（在本目录执行，无需复制令牌）：
- 查看：`python3 kaoyan_cluster_admin.py --ssh hp status`
- 切主：`python3 kaoyan_cluster_admin.py --ssh hp switch W1`（也支持 S1、HP）
- 恢复：`python3 kaoyan_cluster_admin.py --ssh hp recover`

发布回归：`python3 tests/verify_live_release.py`；三机原生证据见报告。
离线维护：`python3 kaoyan_portable.py --help`；已有库 repair 会备份，restore 仅允许新目标。
Docker Compose / kaoyan_hub_server.py 保留为独立开发与旧版兼容路径，不是当前在线复制入口。

边界：首次迁入冻结写入 24.79 秒，后续切主为秒级；HP 协调器仍是单点，少于两个副本时停止确认写入。
W1 默认系统代理异常独立存在；内部 RPC 已隔离，直连 TLS 验收通过，未擅改全局网络设置。
原 elena 进程停止并保留备份；旧业务入口已统一转发正式入口，回滚必须先迁回最新权威快照。
旧 17/18 文档中的快照阶段记录保留为历史；本目录 25 报告与原 17 泳道图为当前实施结论。
English: native Windows deployment, synchronous replication, fenced live switchover and scoped fault acceptance are implemented; see the report for measured limits.
