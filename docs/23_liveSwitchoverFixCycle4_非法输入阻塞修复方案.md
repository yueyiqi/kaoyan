# 第四轮输入故障验收与修复 / Cycle 4 malformed-input recovery
> [IoC_Skill_Telemetry] Status: TAIL_PENDING · Date: 2026-10-24 · Author/Exec: Codex/OpenAI
[K] 三机在线首轮验收已通过 ev:ev-0011；扩展非法数值用例失败 ev:ev-0012。
根因：旧路由直接 int/float 转换抛错；协调器把失败请求保留为 pending，后续请求反复恢复同一个非法输入。
修复：输入转换错误回滚整个请求事务，保存明确的 422 回执后继续队列；数据库/网络故障仍失败关闭。
同时禁止非有限 JSON 数值与字符串 nan/inf，防止 SQLite 非空约束错误被恶意触发为持续 pending。
验收：invalid、nan、null 三种参数均返回 400/422；随后合法写入成功，pending=false，坏请求无部分数据落盘。
English: invalid client input must produce a durable rejection, never poison the recovery queue.


## [IoC_Revision_vLiveFinal]
Status: VERIFIED；非法输入不阻塞队列 ev:ev-0013、ev:ev-0034～0036。
