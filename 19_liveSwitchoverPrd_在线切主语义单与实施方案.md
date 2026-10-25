# 在线切主语义单与 PRD / Live switchover specification
> [IoC_Skill_Telemetry] Status: SPEC_PERSISTED · Author/Exec: Codex/OpenAI · AutoExec: AUTHORIZED
> 日期 Date: 2026-10-24 · srbg10 · 用户明确要求部署 W1 并实施修复闭环。
## 第一性可行性 / Feasibility
[K] 实施前版本仅支持完整快照迁移；当时业务、审计、幂等记录分多次提交，尚不具备跨机原子同步。
[I] 低流量考研平台可采用整库提交快照同步，换取跨 SQLite 版本与三种 OS 的确定性；不承诺 18ms。
工况六维：范围=Windows/Linux/macOS；数据=14 业务表及扩展；负载=本轮并发实测；工期=当前实施轮；人天=1 个执行会话；预算=现有主机与原生 Python，不购置服务。
使用 blade-router / engineering-workflows / test-copilot-buddy；实际执行者 Codex，未声称调用 Argon 或异源专家。
## 语义约束 / Semantics
- 主节点：由 HP 单一协调入口指定、实际执行业务 SQL 的原生工作节点；候选 W1/HP/S1。
- 切主：入口保持不变，请求排队等待当前处理结束；若有未确认请求，持久化新任期后在新主重放，再继续流量。
- 写隔离：工作节点仅在内部认证、匹配 epoch、leader 角色和预期版本时执行；对外没有直写入口。
- 成功确认：完整事务（业务、RBAC 审计、请求回执）提交后，协调器持久化完整快照，至少两个工作节点确认同一内容。
- 请求重放：事务内保存请求指纹和完整响应；同一键不同内容返回冲突，不重复业务副作用。
- 缺表：部署启动补齐结构；运行中缺表报故障，先保留损坏副本再从权威完整快照修复，禁止空表冒充数据恢复。
- S1 替代 M1 是本次用户授权；不更改全域主机定义。
## 架构决策 / Architecture
1. 原有后端路由与 RBAC 保留，以请求级数据库事务封装，避免逐 API 手工复制遗漏。
2. 独立工作进程常驻 W1 原生 Windows、HP Linux、S1 macOS，SQLite 文件使用各自主机原生路径。
3. 内部服务绑定回环；HP 通过受限 SSH 隧道访问 W1/S1；密钥及令牌存入忽略的部署配置，不写入 Git。
4. HP 协调器用持久 SQLite 状态、进程排他锁和请求锁维护单一顺序；原子保存 pending、快照、版本、epoch。
5. 副本安装先验证 SHA-256、完整性、全表摘要，再用 SQLite Backup API 恢复；同一工作节点所有操作互斥。
6. 网络/进程故障允许失败关闭；未确认的 pending 必须恢复或重放后才处理下一请求。
7. 切主前新主安装权威快照；掉线旧主重新加入时接受新 epoch 覆盖其未确认分支。
8. 单协调器并非共识集群；HP 协调器停机时暂停服务。PG18、自动选举和任意故障零停机不属于此次承诺。
## 实施顺序 / Delivery
A. 前置取证和规格落盘 → B. 事务/回执/复制/切主实现 → C. 本地故障回归。
D. W1 常驻服务及全表部署 → HP/S1 部署 → 三机真实 HTTP 联调与故障注入。
E. 修复方案落盘并实施 → 重复验收 → 生产入口受控接入、回滚说明与报告归档。
## 验收矩阵 / Acceptance
| ID | 必须满足的断言 / Required assertion |
|---|---|
| A01 | 三机真实 OS、常驻 PID、实际数据库路径与 14 业务表；W1 必须 Windows 原生 |
| A02 | 空库、旧库、缺表、跨 SQLite 版本恢复；历史密码、账号状态、业务记录保留 |
| A03 | 同一入口持续并发写入时 HP→W1→S1→HP；所有成功记录和回执可追踪且无重复 |
| A04 | 全表内容摘要一致；包含 RBAC、密码轮换、中文/CRLF/BLOB/扩展表 |
| A05 | 副本直写、过期 epoch、错误密钥、幂等冲突拒绝；权限测试保持有效 |
| A06 | 一个副本掉线可继续确认两个副本；不足两个时返回 503，恢复后 pending 收敛 |
| A07 | 当前主故障、协调器重启、响应丢失重放；已确认写入不丢失 |
| A08 | W1 人为丢表后保留坏库、恢复完整数据并复测；不得只检查 HTTP 200 |
| A09 | 真实切换耗时/请求延迟实测，不用本机 OS 标签替代三机证据 |
| A10 | 生产入口、原有功能回归、备份与回滚路径；报告列出所有未覆盖边界 |
## 判断与资料 / Decision references
SQLite 支持单写事务，完成的 Backup API 产生一致快照；本方案将快照纳入确认协议，快照功能本身不等于 HA。
参考：[SQLite transactions](https://www.sqlite.org/lang_transaction.html)；[Backup API](https://www.sqlite.org/backup.html)。
完成定义：以上范围内验收用例通过并附 ev 证据；不声称所有未来输入和故障组合永远无 bug。


## [IoC_Revision_vLiveFinal]
Status: VERIFIED；W1/HP/S1 实装、真机联调及公网验收 ev:ev-0021、ev:ev-0034～0036、ev:ev-0038；实际范围与边界见 25 报告。
