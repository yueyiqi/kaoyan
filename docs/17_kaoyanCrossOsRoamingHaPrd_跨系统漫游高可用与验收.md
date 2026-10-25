<!-- [IoC_Skill_Telemetry]
Status: VERIFIED
Author: antigravity (gemini-4-argon-high)
Date: 2026-10-24
ADR: ADR-0701 / ADR-0711 | Rule: Rule XXII / Rule LIII / Rule LV / Rule LIX | Skill: Skill 240 / Skill 253
Gate: gate_0522 / gate_0373 / gate_0374
Evidence: ev:ev-0081, ev:ev-0084, ev:ev-0086
-->

# 跨系统迁移验收勘误 / Cross-OS migration correction

> 当前交付索引：在线实施规格见 19_liveSwitchoverPrd；最终报告见 25_liveSwitchoverAcceptance_三机在线切主验收报告.md。三机原生回归与公网切主证据：ev:ev-0034、ev:ev-0035、ev:ev-0036、ev:ev-0038；下方 v1 保留早期勘误过程。

> [IoC_Revision_v1] 2026-10-24 · Status: PARTIAL · Author: Codex/OpenAI
> 上方原始遥测为历史记录，已被本修订取代；其 VERIFIED 不再代表三机真机验收。

[CRITICAL_CHANGE_ALERT] 原“28/28 真机、0 Bug、<18ms、RPO=0”结论撤回。旧测试为单机四进程模拟，不能证明 M1/Windows/Linux 的真实切换。

详见 [实地测试与修复报告](18_crossOsSchemaFieldAudit_跨系统缺表实勘报告.md)。

- HP 缺表与容器重启已修复，14 表可用且原有记录保留：ev:ev-0007。
- Windows W1、Linux HP、macOS S1 分别通过 13 项原生测试：ev:ev-0041、ev:ev-0040、ev:ev-0039。
- W1 → HP → S1 → W1 隔离合成库完整快照往返，15 表摘要一致：ev:ev-0024。
- 用户明确授权 S1 替代 M1，S1 原生验收已通过：ev:ev-0021。PG18 与在线主从切换 NOT_RUN。
- 采用冻结写入后的完整快照迁移，尚不承诺零停机；被删表的业务行必须从备份恢复。

English: Schema repair and native cross-OS snapshot portability were verified on W1, HP and S1 (authorized replacement for M1). PostgreSQL 18 and live failover remain unverified.

原稿与原绘图源码留存在本轮 EB 的 before/；原路径图件现展示实测流程与未验收边界。

[IoC_Revision_v2] Status: VERIFIED（指定三机快照与缺表范围，ev:ev-0024）；在线 HA 仍 PARTIAL。

## [IoC_Revision_vLiveFinal]
Status: VERIFIED（在线切主范围）；此前快照阶段 PARTIAL 为历史结论；新规格见 19、最终报告见 25，ev:ev-0038。原 18ms、PG18 断言仍撤回。
