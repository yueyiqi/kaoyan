# 07 · 刀刃路由档位修复（Flash 仅限超机械）与 kaoyan.elenalyl.top 上线阻塞现状

> Status: `IMPLEMENTED`（路由器/拓扑/测试/Skill/AGENTS/ADR）· 闸口 `SPEC_PERSISTED`（延后）· 域名 `BLOCKED_EXTERNAL`
> Author/Exec: Claude Sonnet 5.5 (High) · 关联 ADR-0710 · 伴生脚本：同目录同名 `.py`（只读状态探针）
> 证据：`ev:ev-0021`（109 个 blade 测试 + 一致性校验器）

## 1. 问题：刀刃路由为什么把实机运维派给 Flash

| 层 | 事实（实测） | 结论 |
| :-- | :-- | :-- |
| 拓扑 SSOT | `blade_agent_topology.json` 把 q3、q4 整体路由到 `antigravity`（`gemini-3.8-flash`） | 按「象限」路由，不看任务机械度 |
| 路由器 | `_pack` 对所有非深度任务返回 `flash` | 没有任何降级门槛 |
| 象限 YAML | q3 关键词含「配置文件修改」「批量修改配置」，q4 含「测试」「Commit」「git push」 | 改线上配置、排障被当成「搬砖」 |
| 实例 | 13:23 把「Caddyfile 配置修改、文档落盘、运行现有探针测试」判为 `q3/flash` 并派发 | 误派；修复后同文本判为 `argon`（`ESCALATION_TERMS:caddy,配置文件,caddyfile`） |

## 2. 修复（用户裁决：除超机械才 Flash，否则 Gemini 4 Argon）

| 项 | 内容 |
| :-- | :-- |
| 拓扑 | 新增后端 `antigravity_argon`（`gemini-4-argon-high`）与 `flash_policy`；`antigravity` 保留为 Flash |
| 降到 Flash 的条件 | 须**同时**满足：q3 且命中严格机械词（或「运行现有单测」）、无升档词、无高危词、文本 ≤160 字；否则 Argon |
| fail-safe | 策略缺失 ⇒ Argon；`flash_policy` 校验失败 ⇒ 拓扑不可信 ⇒ 禁止派发 |
| 派发 | Flash 不能被强指派给 Argon 任务（BLOCKED）；Argon 指派给 Flash 任务（升档）免理由 |
| 嵌套执行器 | `low→[flash,sonnet]`，`medium→[argon,sonnet]`，`high→[sonnet]` |
| 披露 | 路由输出 `flash_gate.denied_reasons`、`parent_switch_required` |

改动文件：`.governance/blade_agent_topology.json`、`blade_topology.py`、`blade_router.py`、`blade_nested_contract.py`、`tests/test_blade_router.py`（新增 `T1b_FlashOnlyForStrictMechanical`，9 例）、`tests/test_blade_agent_topology.py`；文档同步：`SKILL.md`（v7）、`nested-routing.md`、`.agents/AGENTS.md`（新增 LXXI）、`llm_routing_quadrant_ssot.yaml` 注记、新 ADR-0710。

## 3. 「还要改什么」的完整清单

| 位置 | 是否已改 | 说明 |
| :-- | :-- | :-- |
| AGENTS（`.agents/AGENTS.md`，`AGENTS.md` 是其软链） | 已改 | 新增 LXXI-A/B；243→247 行，低于 WARN 300 |
| ADR | 已改 | 新建 ADR-0710；ADR-0642 保留，不删（其「q3/q4→Flash」条款被 0710 部分取代） |
| Skill | 已改 | `blade-router/SKILL.md` 契约行 + v7 修订头（只追加，不覆写旧遥测） |
| 闸口 | **未改（延后）** | 见下 |

**闸口为什么延后：** 新增 pre-commit 闸口须遵 AGENTS LXX-A（入册 + 接线，缺一即 PAPER-TIGER）与 LXVI-B（闸口/业务两阶段分层）；且闸口总数处于 LXVIII-B 封顶带，应先合并再新增。当前以回归测试 + `doctor` 的 `gemini_tier_rule` + ADR 一致性校验器兜底。后续 Phase-Gate 建议：把 ADR-0710 的校验器接入现有切片，而不是新增编号。

## 4. 诚实边界（不得夸大）

- `invoke_subagent` 的 `Model` 枚举只有 `inherit/flash_lite/flash/pro`，**选不到 Argon**；`pro` 不是 Argon。
- 路由器对 Argon 只输出 `PLANNED` + `parent_switch_required=true`，从不声称已调用。
- `agy -p --model gemini-4-argon-high` 通道 13:48 探针失败（`Eligibility check failed … EOF`，本机网络），状态 `NOT_RUN`。
- 这些改动在 `srbg10` 工作树，且超出本节点 `write_acl_scope`，**尚未提交、未推送**；需合入母舰才长期生效，否则可能被同步覆盖。

## 5. 截图问题（`kaoyan.elenalyl.top` 仍 `ERR_CONNECTION_CLOSED`）再分析

14:01 复测，与 13:35、13:49 完全一致，没有新问题：

| 层 | 证据 | 结论 |
| :-- | :-- | :-- |
| 注册局 | RDAP 仍 `client hold`，自注册起未变 | 唯一阻塞 |
| 万网 DNS | `kaoyan` → `43.160.227.166` | 用户配置正确 |
| 公共 DNS | `223.5.5.5`、`8.8.8.8` 均为空 | `.top` 根不发布委派 |
| 边缘 | 强制解析到 `43.160.227.166`，80 返回 308 | 回源链路就绪，缺证书（证书需公网可解析） |
| 守护 | launchd 每 300 秒、上次退出码 0，最新日志 `WAITING` | 已布防，解封后自动重载并清缓存 |

结论：服务器侧无缺陷，没有可实施的修复；解锁只能由用户在阿里云「域名控制台」完成实名认证。

## 6. 路由记录（本方案自身如何走刀刃路由）

- 截图任务文本经修复后的路由器：`q4 → argon → gemini-4-argon-high`，`PLANNED`，`invoked=false`，`parent_switch_required=true`，`flash_gate.denied_reasons=[DECISION_NOT_STRICT_MECHANICAL, ESCALATION_TERMS:dns,证书,方案]`。
- 本轮会话为 Claude Sonnet 5.5，**未**起子代理：Argon 无法从此处选择，也**不得**降到 Flash；剩余工作只有只读复测与落盘，由本会话直接完成。
- 若后续需要 Argon 执行（例如解封后的上线验证），请把会话切到 Gemini 4 Argon 再派发。
