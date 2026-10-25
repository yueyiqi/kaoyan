<!-- [IoC_Skill_Telemetry] Status: PARTIAL; Author: Codex/OpenAI; Node: srbg10; Date: 2026-10-24 -->
# 跨系统数据库缺表实勘与修复报告 / Cross-OS schema field audit

Status: VERIFIED（缺表修复、W1/HP/S1 原生测试与快照迁移）；PARTIAL（PG18 与在线主从切换）。用户于 2026-10-24 明确授权以 S1 替代 M1。
Evidence root: `_ephemeral_blackbox/2026-10/eb_20261019_srbg10_H_codex_gpt-6_kaoyan-cross-os-schema-field-audit`。

## 实地结果 / Field results

| 对象 / Target | 实测 / Observation | 结论与证据 / Verdict and evidence |
|---|---|---|
| HP Linux x86_64 | 原容器持续重启，`no such table: schema_migrations`；挂载 `/app/migrations`，代码读取 `/app/db_migrations`；持久卷实际有 8 表 | [K] 已修复，14 表健康 HTTP 200，8 张原表已有记录逐行保留；ev:ev-0007 |
| HP 原生 Python 3.14.4 / SQLite 3.46.1 | 13 项缺表、迁移、并发、回滚与 HTTP 健康回归 | [K] PASS；ev:ev-0040 |
| W1 Windows 11 AMD64 | 原 `python` 是不可用的商店占位符；旧探针通过 WSL 运行 Linux | [K] 隔离部署官方便携 CPython 3.13.9；Windows 原生 13 项测试通过；ev:ev-0041 |
| 本机 M4 macOS arm64 | Python 3.14.5 / SQLite 3.50.4，13 项同源测试 | [K] PASS；ev:ev-0009；不能冒充 M1 |
| S1 macOS 27.0.1 arm64 | 原生 Python 3.9.6 / SQLite 3.54.0，13 项同源测试 | [K] PASS；ev:ev-0039；按用户授权替代 M1 |
| 原目标 M1（已替换） | 先前 SSH 不可达 | 历史失败 ev:ev-0003；不再作为本轮阻塞项 |
| 真实跨机数据往返（隔离合成库） | W1 → HP → S1 → W1，14 张应用表 + 1 张未知扩展表，各表列、行数和完整 SHA-256 一致 | [K] PASS；ev:ev-0024；含中文、音标、CRLF、Windows 路径及 BLOB |
| PostgreSQL 18 / Docker 多架构 / 在线漫游 | 本轮 HP 实际使用 SQLite；W1 原生进程，不是 Windows Docker；S1 为原生进程测试 | NOT_RUN，不据此声称 PG18、RPO=0、零停机或毫秒级切主 |

## 纸面差异与根因 / Claims versus evidence

1. [K] 原 `ev-0084` 的 28 场景在一台机器启动四个 Python 进程；`KAOYAN_OS_FAMILY` 是标签，非实测 OS。该证据只能说明当时的本机协议模拟。
2. [K] 原验证器读取 `/tmp/kaoyan_v4_work/kaoyan_hub_server.py`，并非仓库发布入口；本仓根入口和 `backend/` 副本也已分叉。
3. [K] 原图中的“10 表、三系统 100%、0 Bug、<18ms、RPO=0、四节点仲裁”未由真实跨机证据支持，全部撤回为未验证设计目标。
4. [K] 原健康查询吞掉缺表异常并把行数记成 0，可能返回假正常；新接口在结构不完整时返回 HTTP 503，查询本身不改库。
5. [K] 本次真实跨机测试发现 Backup API 在不同 SQLite 版本重写快照文件头；整文件摘要误判。恢复现改为复制已完成的静态快照，再验证完整性、结构及逐表摘要。失败 ev:ev-0008，修复后 ev:ev-0011、ev:ev-0024。
6. [K] S1 首轮 WAL 快照只读校验报 unable to open database file（ev:ev-0020）；独立备份改为 DELETE 日志模式以消除 WAL/SHM 附件依赖，三机回归通过（ev:ev-0021～0023）。源库保持原 WAL 设置。

## 实装范围 / Implemented scope

- `V005__complete_portable_schema.sql` 是 14 表完整结构；`kaoyan_schema.py` 在事务内创建缺表、补兼容列、检查版本摘要与索引。异常回滚，不吞 DDL 错误。
- 缺表修复只恢复结构，不能找回该表已丢失的业务行；丢失行须从备份或可信副本恢复。
- 启动时不重置已有账号密码、令牌、角色或停用状态。`backend/kaoyan_hub_server.py` 统一调用根入口。
- 镜像内包含迁移文件；数据库固定由 `KAOYAN_DB_PATH` 指向持久卷，原生 Windows/macOS/Linux 使用本机路径语义。端口由 `KAOYAN_PORT` 提供。
- `kaoyan_portable.py` 提供 inspect / repair / export / restore。导出使用 SQLite Backup API，包含已提交 WAL、全部表及未知扩展；不执行 CRLF 或路径字符串改写。
- 恢复只接受新目标文件，校验完整 SHA-256、数据库完整性、版本结构和逐表摘要，再以不覆盖方式发布。既有数据库不会被覆盖。
- HP 备份：`/home/hp/kaoyan_english_hub/db_backups/schema_field_20261019/`；保留旧容器 `kaoyan-before-schema-20261019`。恢复服务后再回退须先保全新增写入。
- W1 隔离验证包：`C:\Users\lenovo3\_workspace_kaoyan_schema_20261019`，未修改系统 PATH；可复用同包启动后端。S1 验证包位于 `/Users/baigong/_workspace_kaoyan_schema_20261019`；未改动系统 Python。

## 验收边界 / Acceptance boundary

最终 W1、HP、S1 三个原生 OS 各 13 项测试，合计 39 次断言组执行；另有一次真实三段传输快照往返。它们证明所列环境中的可移植快照恢复，不证明无限场景无故障。
测试覆盖：全新库、旧 V001 库、14 张表逐表缺失、缺列、主键不兼容、版本摘要漂移、迁移文件缺失、并发初始化、WAL、中文/二进制、损坏包拒绝、禁止覆盖、账号保持、HTTP 503。
最终快照切换必须先停止源应用写入，导出并校验目标，启动目标后再切换入口。新写入不会自动追到既有快照；未实现分布式仲裁或连续复制，因此不承诺零停机/RPO=0。
剩余独立验收：PG18、写入围栏、断网、追平与在线切主。M1 已由用户授权 S1 替代，W1 → HP → S1 → W1 数据往返通过（ev:ev-0024）。

## 可重复执行 / Reproduction

在项目目录使用当前原生 Python 执行 `python tests/test_portable_schema.py`；测试使用隔离临时库，不读写生产数据库。
迁移操作用 `python kaoyan_portable.py --help` 查看契约；`repair` 自动留存既有库备份，`restore` 必须提供不存在的目标文件。
旧 28 场景脚本现要求显式 `--server` 与 `--report`，报告固定标明 `LOCAL_PROCESS_SIMULATION_ONLY`，不会将模拟 OS 标签标成真机。

前置限幅：复用现有需求外专输出场景，再以原生 OS、源码 SHA、缺表注入和数据摘要取证；Codex/OpenAI 执行核心修复，Python/SSH 执行确定性探针。未声称异源 LLM 已复核。
工况：3 个目标节点 W1/HP/S1；本机 M4 的先期回归作为补充证据。工期、人天和预算未获给定，不伪造估计。

依据：[SQLite WAL 只读与附件约束](https://www.sqlite.org/wal.html#read_only_databases)；[SQLite Backup API](https://www.sqlite.org/backup.html)；[SQLite 跨平台文件格式](https://www.sqlite.org/onefile.html)；[官方 Windows 便携 Python 包](https://www.python.org/downloads/release/python-3139/)。

[CRITICAL_CHANGE_ALERT] 原图与文档的未经支持验收结论已纠正，原稿保存在本轮 evidence root 的 `before/`。本报告取代旧版结论，不降低用户要求的最终三机在线迁移目标。

[IoC_Revision_v1] Status: PARTIAL。最终应用层 POST 持久化、幂等重放与缺表 503 在 M4/HP/W1 通过：ev:ev-0016、ev:ev-0017、ev:ev-0018。最终 HP 镜像内源码 SHA 与工作区一致，重启计数为 0，原记录保留：ev:ev-0019。

[IoC_Revision_v2] Status: VERIFIED（W1/HP/S1 缺表与快照范围），在线 HA 仍 PARTIAL。S1 已按用户授权替代 M1；最终同源回归 ev:ev-0021、ev:ev-0022、ev:ev-0023，真实三机往返 ev:ev-0024。

[IoC_Revision_v3] 最终 HP 发布复核：镜像源码含 S1 WAL 修复、14 表健康、重启计数 0、8 张原表旧记录保留，ev:ev-0026。原路径图件已同步 S1，ev:ev-0025。

[IoC_Revision_v4] 入口按配置、存储、权限、读取、账号写入、业务写入分拆，消除旧双份入口与单文件超载；三机最终回归（含账号权限拒绝）ev:ev-0028、ev:ev-0029、ev:ev-0030；最终镜像与源码一致、健康与原记录保留 ev:ev-0031。

[IoC_Revision_v5] 提交前拦住并行引入的默认密码重置分支；保留兼容接口字段，三机最终回归 ev:ev-0033、ev:ev-0034、ev:ev-0035，最终 HP 发布复核 ev:ev-0037。旧模拟器拒绝将当前发布入口当作实验漫游服务验收（ev:ev-0036）；完整 28 场景未重跑。

提交检查的存量告警：HP 部分隧道凭据配置、流水线 A hook 尚未安装、部分历史遥测字段不足；本轮未改动这些独立设施。

[IoC_Revision_v6] 启动仅补缺行，保留既有角色/权限描述、授权者和迁移时间；重启前后全表摘要不变已在 S1/HP/W1 验收（ev:ev-0039、ev:ev-0040、ev:ev-0041）。最新 HP 镜像及旧记录复核 ev:ev-0043；中间构建连接中断导致的旧镜像摘要不符 ev:ev-0042 亦保留。跨机往返为隔离合成库，HP 生产库实施缺表修复，未切换生产流量到 W1/S1。

[IoC_Revision_v7] 实际运行中的 HP 发布容器（Python 3.11.16 / SQLite 3.46.1）也执行同一套隔离临时库测试，13 项通过；包含真实 HTTP 写入、权限拒绝、缺表 503 和全表重启保持：ev:ev-0045。生产库未被测试写入。
