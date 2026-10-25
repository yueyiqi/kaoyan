# 生产真源对账与切入方案 / Production authority and cutover
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] 现有公网 kaoyan.liuzengyu.top 优先回源 elena，HP 仅备用；并非三机协调入口。
[K] elena 默认 db_volume 是闲置八表旧库，实际运行进程使用 kaoyan_storage/hot_db；ev:ev-0019 的默认路径比较不作为生产真源证据。
[K] 按进程环境修正取证后 ev:ev-0020：实际主库 16 表，含 14 业务表及两张旧扩展表；HP 备用 14 表，内容不相同。
裁决：以实际公网主库为权威，完整迁移全部 16 表，再增加两张新协议表；保留 HP 原备用库，不覆盖其历史证据。
拓扑断言：① 现有 HTTPS 入口保持；② CVM 仍只有 Caddy 边缘代理；③ HP 单协调器 + W1/HP/S1 原生执行节点；④ 库数据置于各机独立 production.sqlite3。
切入：最终回归通过 → 冻结旧主和旧备用写入 → 完整备份实际主库 → 启动三机生产配置 → 校验所有历史表行 → 更新业务反代到已有 HP 通道。
旧 elena 业务进程停用，旧别名入口转发至同一正式入口，防止两个可写分支继续漂移；其他业务路由不变。
回滚：在公网切入前失败可恢复旧服务；切入后必须先将协调器权威快照回灌旧库，禁止直接启动旧快照导致数据倒退。
端点：elenalyl.top 当前仍无正常解析/证书；本轮使用已上线 kaoyan.liuzengyu.top，不把域名注册问题伪报为数据库缺陷或已经修复。
English: migrate the running public authority, retain both legacy backups, and move all write entry points behind one coordinator.

## [IoC_Revision_vLiveFinal]
Status: VERIFIED；以实际 hot_db 完成迁入、公网切换及全历史行保留 ev:ev-0022、ev:ev-0038。
