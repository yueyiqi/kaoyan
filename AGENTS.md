# 在线迁移维护契约 / Live migration maintenance contract
> [IoC_Skill_Telemetry] Status: IMPLEMENTED · Codex/OpenAI · ev:ev-0029
- 唯一生产写入入口是协调器；不得直接启动旧业务服务器连接生产 SQLite 文件。
- 确认响应必须晚于协调器持久化及两个副本内容确认；禁止把单机提交等同于跨机成功。
- 账号、权限、审计、业务行和请求回执须同事务；坏输入不得堵塞 pending 队列。
- 恢复须比较全表内容及完整 DDL；运行中缺表用完整副本恢复，不以新建空表冒充恢复数据。
- 改动协议运行 tests/test_live_cluster.py；改动库表运行 tests/test_portable_schema.py；前端请求改动运行 tests/test_network_retry.js。
- 复用 engineering-workflows / test-copilot-buddy；已有 pre-commit Guardrail 必须执行真实测试并绑定源码摘要。
- 真机验收保留 W1 Windows、HP Linux、S1 macOS 实际 OS 证据；本机进程模拟不得贴真机标签。
- 部署后必须核验各机源文件摘要；生产回滚先回灌权威快照，不得退回旧数据。
- 详细契约、边界和证据见 19 规格及 25 验收报告；Status 按新一轮证据追加修订。

- 管理下钻验收必须按实际元数据对账并覆盖分页、零匹配、外键精确定位、嵌套凭据脱敏与登录/注销竞态；运行 tests/verify_live_release.py，源码含字段名不可代替行为检查。
