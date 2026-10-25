# 第二轮接线验收与修复 / Cycle 2 native integration repair
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] 原生任务已启动：W1 Windows PID 54296；HP Linux、S1 Darwin 均可读取实际库表。
[K] 接线发现：HP→W1 SSH 隧道 publickey 被拒绝，不能把部署命令成功当作链路验收。
根因：W1 sshd_config 没有 Match administrators，使用用户 .ssh/authorized_keys；部署脚本误投管理员公钥文件。
修复：受限专用公钥写入实际用户文件，仅允许转发到本业务回环端口；保持已知主机指纹校验。
修复脚本自身曾将单元素字符串取 [0] 变成首字符 r；已删除本次无效行并写入完整受限公钥。
验收：从 HP 实际 RPC 查询 W1 的 Windows 系统、PID、库路径和 16 表（14 业务 + 2 协议表）。
同时：ev:ev-0004 的丢响应用例使用不同 JSON 空格，触发符合约定的原始字节指纹冲突；修正夹具使用相同请求字节。
本地七组回归：ev:ev-0005；生产线上入口仍未切换，不外推为生产验收。
English: repair the actual Windows key-file wiring; verify through HP rather than relying on task creation success.

## [IoC_Revision_vLiveFinal]
Status: VERIFIED；实际 Windows RPC 接线与完整部署 ev:ev-0007、ev:ev-0021。
