# 第三轮权限验收与修复 / Cycle 3 ownership and retry repair
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] 新增跨用户资料隔离测试失败：ev:ev-0008。普通用户可通过猜测 span_id 修改他人批注。
根因：旧版批注与作文 UPSERT 仅按全局 ID 冲突更新，未验证现有行的 user_id；批注升格也缺少归属验证。
影响：迁移正确复制库表仍可能携带错误权限行为；必须一起修复后再上线。
修复：写入前读取 owner，非本人立即 403；批注升格和关联同样校验；事务封装消除检查与更新竞态。
扩展：浏览器原有写请求无稳定幂等键，且部分调用吞掉网络错误；新增仅针对同源 API POST 的有界重试与明确失败提示。
验收：批注覆盖、批注升格、作文覆盖跨用户均 403，原文不变；前端重试保持请求键与请求体不变，重试耗尽显示“未确认”。
English: repair object ownership checks and preserve request identity during bounded browser retries.


## [IoC_Revision_vLiveFinal]
Status: VERIFIED；权限与浏览器回归 ev:ev-0010、ev:ev-0021、ev:ev-0024。
