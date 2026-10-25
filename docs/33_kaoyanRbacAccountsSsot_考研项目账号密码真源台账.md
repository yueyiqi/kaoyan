> [IoC_Skill_Telemetry]
> Status: IMPLEMENTED
> Author: Antigravity (qwen3.8-max / gemini-4-argon-high)
> Date: 2026-10-25
> Skill: slot-artifact-persistence, completion-evidence-protocol
> Trigger: 用户上传 kaoyan-elena.duckdns.org 圈红登录框截图，询问对应账号密码是否在项目 SSOT 中，要求找出并落盘为项目 SSOT (ev:ev-0005)

# 33 · 考研英语精读工作台 (`kaoyan-elena.duckdns.org`) 圈红登录框对应账号密码 SSOT 真源台账
# (KaoyanEnglish Hub RBAC Login Accounts & Passwords Single Source of Truth Ledger)

> **实施状态 (`Status`)**: `IMPLEMENTED` (`ev:ev-0005`)
> **项目级机器真源 (`Project SSOT JSON`)**: [`.bz/95_kaoyan_考研/kaoyan_rbac_accounts_ssot.json`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/kaoyan_rbac_accounts_ssot.json)
> **全域治理真源镜像 (`Governance SSOT JSON`)**: [`.governance/kaoyan_rbac_accounts_ssot.json`](file:///Users/liuzengyu/treeworker/workers/srbg10/.governance/kaoyan_rbac_accounts_ssot.json)
> **后端哈希与鉴权实现**: [`kaoyan_runtime.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/kaoyan_runtime.py) (`SEED_USERS` / `PBKDF2-HMAC-SHA256`)

---

## 一、核心直答：圈红登录框对应的账号密码此前在项目 SSOT 中吗？

1. **取证结论 (`[K]` `ev:ev-0005`)**：
   - **此前状态（半散落态，缺独立机器可读 SSOT）**：
     - 后端源码 [`kaoyan_runtime.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/kaoyan_runtime.py) 与生产库 `production.sqlite3` (`sys_users` 表) 中仅存储了 `PBKDF2-HMAC-SHA256`（10,000 次迭代 + 独立盐值）的 64 位十六进制密码摘要（代码零明文密码）；
     - 初始明文密码仅曾作为章节表格出现在 [`18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.md`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/18_kaoyanRbacAccountMgmt_%E8%B4%A6%E5%8F%B7%E6%9D%83%E9%99%90%E7%AE%A1%E7%90%86%E4%B8%8E%E9%AA%8C%E6%94%B6%E6%8A%A5%E5%91%8A.md) 中，**在 `.bz/95_kaoyan_考研/` 与 `.governance/` 下均缺失专门的账号密码 SSOT 独立真源台账**。
   - **本次治理闭环 (`ev:ev-0005`)**：
     - 已从生产主库 `production.sqlite3` (`W1` + `HP` + `S1` 三节点同步库) 提取全部 10 条 `sys_users` 记录，经 `PBKDF2-HMAC-SHA256` 密码学逆向核验及公网 `https://kaoyan-elena.duckdns.org/api/auth/login` 实测登录（5 个活跃账号全部返回 `HTTP 200`），正式双点落盘为项目 SSOT：
       1. [`.bz/95_kaoyan_考研/kaoyan_rbac_accounts_ssot.json`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/kaoyan_rbac_accounts_ssot.json)
       2. [`.governance/kaoyan_rbac_accounts_ssot.json`](file:///Users/liuzengyu/treeworker/workers/srbg10/.governance/kaoyan_rbac_accounts_ssot.json)
       3. [`.bz/95_kaoyan_考研/33_kaoyanRbacAccountsSsot_考研项目账号密码真源台账.md`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_%E5%89%8D%E6%B2%BF%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%8E%A2%E7%B4%A2%E9%AA%8C%E8%AF%81/95_kaoyanEnglishHub_%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD%E7%B2%BE%E8%AF%BB%E5%B9%B3%E5%8F%B0/33_kaoyanRbacAccountsSsot_%E8%80%83%E7%A0%94%E9%A1%B9%E7%9B%AE%E8%B4%A6%E5%8F%B7%E5%AF%86%E7%A0%81%E7%9C%9F%E6%BA%90%E5%8F%B0%E8%B4%A6.md)

---

## 二、截图圈红区域 (`kaoyan-elena.duckdns.org`) 对应登录账号与密码全量 SSOT 表 (`ev:ev-0005`)

截图中圈红组件对应前端 DOM：左框 `id="scholarUserInput"`（占位符：`账号 (学籍/管理员)`）、右框 `id="scholarKeyInput"`（占位符：`掩码密码 (······)`）、按钮 `id="loginSubmitBtn"`（`🔑 登录并恢复进度`）。

### 2.1 现役可登录活跃账号 (`ACTIVE` — 5 个账号全部实测 `HTTP 200` 通过)

| 序号 | 角色分级 (`role`) | 权限层级 | 圈红左框输入：**账号 (`username`)** | 圈红右框输入：**密码 (`passcode`)** | 显示名称 (`display_name`) | 盐值 (`passcode_salt`) | `PBKDF2-HMAC-SHA256` 生产库摘要前缀 | 公网登录实测 (`kaoyan-elena.duckdns.org`) |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | **`ADMIN` (系统管理员)** | `L100` | **`admin`** | **`Kaoyan@Admin2026`** | 系统管理员 (`admin`) | `salt_admin_2026` | `d567d098a5c267dc...` | ✅ `HTTP 200` (`ev:ev-0005`) |
| **2** | **`ADMIN` (系统管理员)** | `L100` | **`commander`** | **`Kaoyan@Admin2026`** | 统帅 (集群架构管理员) | `salt_cmd_2026` | `b698890defe2ff1f...` | ✅ `HTTP 200` (`ev:ev-0005`) |
| **3** | **`SCHOLAR` (正式研友学籍)** | `L50` | **`colleague_a`** | **`kaoyan2026`** | 同事 A (考研英语主理人) | `salt_6c5c88bf59` | `bf66b0839ef00eb7...` | ✅ `HTTP 200` (`ev:ev-0005`) |
| **4** | **`SCHOLAR` (正式研友学籍)** | `L50` | **`scholar_b`** | **`kaoyan2026`** | 研友协作学籍 (`scholar_b`) | `salt_schb_2026` | `f2b7a73a26d66873...` | ✅ `HTTP 200` (`ev:ev-0005`) |
| **5** | **`SCHOLAR` (正式研友学籍)** | `L50` | **`scholar_c`** | **`kaoyan2026`** | 测试研友 (`scholar_c`) | `salt_ed3574f5bf` | `747b37d00ae48f6f...` | ✅ `HTTP 200` (`ev:ev-0005`) |

### 2.2 角色权限差异对照（登录后界面解锁行为）

- **使用 `admin` 或 `commander`（密码均为 `Kaoyan@Admin2026`）登录后**：
  1. 解锁 100% 考研英语真题全文（解除 Para 2~4 的 45% 渐变毛玻璃与 25% 学籍锁闭区）及全部精读笔记卡；
  2. 解锁顶部导航第 4 专题页 **「🛡️ 4. 账号与 RBAC 权限管理」** 与 **「🗄️ 5. 全库 5 层 18 表 146 字段管理下钻」**；
  3. 可在后台直接可视化新增账号、重置任意用户密码、切换 `ADMIN/SCHOLAR` 角色或启停状态。
- **使用 `colleague_a`、`scholar_b` 或 `scholar_c`（密码均为 `kaoyan2026`）登录后**：
  1. 解锁 100% 考研英语真题全文精读、5500 考纲词库、个人高频生词账本与阅读进度断点云端同步；
  2. 可在账号面板查看本人权限清单并凭原密码修改本人登录密码；
  3. 遵循零信任 RBAC 隔离（`Rule LVIII`）：不展示全库管理后台，且直接请求 `/api/admin/*` 接口会被服务端刚性拦截返回 `HTTP 403`。

### 2.3 生产库中已自动禁用的历史验收临时账号 (`DISABLED` — 5 个)
生产库 `sys_users` 中另有 5 个由自动化验收脚本创建并在验收完毕后自动设为 `DISABLED` 的一次性账号（`accept_c2ce5ef1`、`accept_e384b5c6`、`accept_f6cbfb7b`、`docker_accept_00567960`、`docker_accept_03ad80b2`），均已封存禁止登录，不影响正常业务。
