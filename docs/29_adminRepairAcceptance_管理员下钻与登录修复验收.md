# 管理员下钻与登录修复验收 / Administrator repair acceptance
> [IoC_Skill_Telemetry] Status: VERIFIED · Codex/OpenAI · srbg10 · 2026-10-24 · ev:ev-0023 / ev:ev-0030 / ev:ev-0029
结论：已发现的13类缺陷均完成修复；本报告已执行范围内，已知未解决缺陷为0。此结论不代表所有未来输入和环境永远无缺陷。
|缺陷|初测问题|最终修复|验证证据|
|---|---|---|---|
|B01|登录无反馈、成功留在学习页、重复点击告警|忙碌去重；成功进入后台并隐藏凭据框|ev:ev-0026 / ev:ev-0030|
|B02|前50/30行截断|稳定分页、真实总数、前后页|ev:ev-0026 / ev:ev-0023|
|B03|零匹配回落全表、空表伪造行|保持真实空集|ev:ev-0023 / ev:ev-0030|
|B04|外键不传目标值、账号写死|精确关联过滤、动态账号|ev:ev-0023 / ev:ev-0030|
|B05|静态字段/约束漂移、新表不可达|实际元数据驱动目录与详情|ev:ev-0026 / ev:ev-0023|
|B06|关联漏查target/owner、数量截断|所有实际关联列OR匹配并COUNT|ev:ev-0026|
|B07|嵌套JSON与编码回执暴露凭据|递归脱敏并保留结构|ev:ev-0026 / ev:ev-0023|
|B08|失败旧数据、乱序回写、退出残留|请求与会话代次校验、清空提示|ev:ev-0026|
|B09|空值混淆、截断、特殊字符拼接|NULL/空串分开、完整折行、数据属性|ev:ev-0026|
|B10|源码字符串命中冒充行为验收|改真实数据/HTTP/状态机/浏览器证据；重生成保留更正|ev:ev-0026 / ev:ev-0023 / ev:ev-0030 / ev:ev-0037|
|B11|旧进程占端口导致新增脚本404|核验PID与配置后交回服务管理器|ev:ev-0014 / ev:ev-0029|
|B12|小屏固定导航遮挡、页面横向溢出|导航随文滚动、网格最小宽度及表格容器约束|ev:ev-0030|
|B13|审计摘要漏显示actor_role|补齐角色值并明确摘要与全流水入口|ev:ev-0022 / ev:ev-0030|
本地集成回归：35项Python测试、7项前端状态场景及请求重试测试通过；ev:ev-0026。
三个实际OS回归：macOS、Linux、Windows各执行同一35项Python用例；ev:ev-0012, ev:ev-0013, ev:ev-0015；不把重复平台运行计为新用例。
公网HTTPS：467/467检查通过；18表、146字段；当时318记录/32页均可达；401、精确过滤、脱敏、只读版本不变及3副本确认；ev:ev-0023。
真实浏览器：16项观察覆盖两管理员首次登录、会话恢复、全字段目录、分页、空集、外键、JSON、三主题；新控制台错误0；ev:ev-0030。
最终部署：17个发布文件在三个实际OS摘要一致，实际HTTP返回脚本亦匹配；ev:ev-0029。
覆盖边界：真实浏览器为内嵌浏览器377px视口；完整桌面浏览器矩阵、生产破坏性注入、大规模压力测试为NOT_RUN。凭据字段保留名称但值脱敏；全记录通过分页访问。
方案、初测和原始JSON证据位于 `_ephemeral_blackbox/2026-10/eb_20261022_srbg10_H_codex_gpt-6_kaoyan-admin-audit-login-fix/`；线上入口 https://kaoyan-elena.duckdns.org 。
工程边界：既有治理基线仍为9 PASS / 3 WARN / 1 BLOCK（冻结豁免）；并行任务改动单独盘点保留，不混入本任务验收。
English: All 13 identified defect categories are resolved within the executed scope; untested environments are explicitly listed above.

[IoC_Revision_v1] Status: VERIFIED · 最终文案去除旧关联表数；最终三机源码/实际响应 ev:ev-0033，最终浏览器16项观察 ev:ev-0032；未新增未解决缺陷。
