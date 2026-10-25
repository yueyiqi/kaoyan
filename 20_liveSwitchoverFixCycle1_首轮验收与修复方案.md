# 第一轮验收与修复方案 / Cycle 1 findings and repair
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] 初始五组本地进程测试通过：ev:ev-0001；三机常驻部署命令执行成功：ev:ev-0002，后者尚不是业务验收。
[K] 新增结构迁移回归失败：ev:ev-0003。源库仅新增 custom_display_name 索引，副本表内容相同，索引未复制。
根因：安装优化仅比较表行摘要，没有比较 sqlite_master 中的完整 DDL。
影响：索引、触发器、视图等结构差异可能被静默遗漏，纸面“完整迁移”未成立。
修复：快照和节点状态同时携带完整结构 SHA-256；安装及确认同时比较结构与每表内容。
保留完整 Backup API 恢复，禁止只重建本次测试索引；后续未知索引/触发器/视图同样纳入。
验收：结构回归先红后绿；扩展提交后响应丢失重放测试；本地完整套件复测后部署修订版。
范围：测试仅操作隔离库；业务生产数据库尚未切入新入口。
English: schema-only drift reproduced; add full sqlite_master hashing to snapshot, install and acknowledgement checks.


## [IoC_Revision_vLiveFinal]
Status: VERIFIED；结构摘要修复回归 ev:ev-0005、ev:ev-0034～0036。
