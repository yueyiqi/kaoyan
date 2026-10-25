<!-- [IoC_Skill_Telemetry]
Status: VERIFIED (ev:ev-0014)
Author: antigravity (gemini-4-argon-high)
Date: 2026-10-24
Deliverable: 18_kaoyanRbacAccountMgmt_账号权限管理与验收报告
Evidence: ev:ev-0014
-->

# 考研英语精读平台 (`KaoyanEnglish Hub v3.4`) 登录后专题 RBAC 账号权限管理系统与零 Bug 验收报告 (`Deliverable #18`)

> **Status**: `IMPLEMENTED` & `VERIFIED` (`ev:ev-0014` · `38/38 PASS` · `0 Bug`)
> **受治落盘路径**: [18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.md)
> **自动化审计引擎**: [kaoyan_unauth_preview_blur_shunt_engine.py](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/shunt/kaoyan_unauth_preview_blur_shunt_engine.py)
> **四模态伴生资产**: [18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.png) | [18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.svg](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.svg) | [18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.pptx](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.pptx) | [18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/18_kaoyanRbacAccountMgmt_账号权限管理与验收报告.html)
> **生产代码锚点**: [index.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/index.html) | [kaoyan_hub_server.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_hub_server.py) | [kaoyan_auth.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_auth.py) | [kaoyan_http_accounts.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_http_accounts.py) | [kaoyan_repository.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_repository.py)

---

## 一、 管理员 (`ADMIN`) 与普通用户 (`SCHOLAR`) 登录账号及初始密码交付表

> **安全声明**：以下密码在页面 HTML、前端 JS 与后端源码中**均不以明文出现**（后端数据库仅存储 `PBKDF2-HMAC-SHA256` 10,000 次迭代 + 独立随机盐值的 64 位十六进制摘要；前端所有密码框默认 `type="password"` 掩码显示且操作后立即清空 DOM，不在页面留存记忆）。

| 角色分级 (`role`) | 权限等级 (`role_level`) | 登录账号 (`username` / `user_id`) | 初始登录密码 (仅在此报告交付，页面零展示) | 显示名称 (`display_name`) | 登录后在『账号与RBAC管理』专题页的权限范围 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`ADMIN` (系统管理员)** | `L100` | **`admin`** | **`Kaoyan@Admin2026`** | 系统管理员 (`admin`) | 全量业务精读 + **查看全量账号台账、手工新增账号 (`ADMIN`/`SCHOLAR`)、强制重置任意账号密码、切换角色与启停状态、查阅 RBAC 安全审计流水** |
| **`ADMIN` (系统管理员)** | `L100` | **`commander`** | **`Kaoyan@Admin2026`** | 集群统帅管理员 (`commander`) | 同上（具备完整 `L100` 系统管理员权限） |
| **`SCHOLAR` (普通用户)** | `L50` | **`colleague_a`** | **`kaoyan2026`** | 同事 A (考研英语主理人) | 100% 真题全文精读、个人词频账本、作文语料与四轨导入 + **查看本人权限、凭原密码修改本人密码**（严禁查看或管理其他账号，调用管理接口刚性拦截 `403`） |
| **`SCHOLAR` (普通用户)** | `L50` | **`scholar_b`** | **`kaoyan2026`** | 研友协作学籍 (`scholar_b`) | 同上（普通用户独立学籍空间，与 `colleague_a` 数据隔离） |
| **`SCHOLAR` (普通用户)** | `L50` | **`scholar_c`** | **`kaoyan2026`** | 研友协作账号 C (`scholar_c`) | 同上（由管理员通过 RBAC 中心创建并完成端到端验收测试） |

---

## 二、 密码默认掩码与页面零记忆安全设计 (Zero-Memory Masked Password Architecture)

针对您指出的「**普通用户或管理员登录的密码都必须是默认掩码且不记录记忆在页面**」，我们在前端、网络传输与后端存储三层实施了刚性闭环：

1. **移除页面一切明文口令与代填入口 (`Zero Plaintext on Page`)**：
   - 彻底移除了顶栏登录横幅中原有的明文口令提示及 `fillDemoScholar()` 一键填入密码函数，前后端源码扫描确认零明文密码字符串。
2. **全站 6 处密码输入框强制掩码与防浏览器自动记忆 (`Masked & Anti-Autofill`)**：
   - 顶栏登录密码框 (`#scholarKeyInput`)、本人改密三框 (`#selfOldPwd`, `#selfNewPwd`, `#selfConfirmPwd`)、管理员建号初始密码框 (`#adminNewPwd`)、管理员重置密码框 (`#adminResetPwd`) 全部显式配置：
     `type="password" value="" autocomplete="new-password" data-lpignore="true" data-form-type="other"`。
3. **操作瞬间擦除 DOM 密码值 (`Immediate DOM Wipe`)**：
   - 实装 `clearAllPasswordInputs()` 函数：在页面初始化 (`DOMContentLoaded`)、点击登录 (`loginWithCredentials`)、安全退出 (`toggleScholarAuth`)、本人修改密码 (`submitSelfPasswordChange`)、管理员创建账号 (`submitAdminCreateUser`)、管理员重置密码 (`submitAdminResetPassword`) 的第一时间，立即将所有密码输入框 `.value` 擦除为 `""`。
   - 浏览器 `localStorage['kaoyan_auth']` 仅保存脱敏会话状态 `{role, userId, displayName, token, lastPara, streakDays, permissions}`，**绝不存储任何明文或哈希密码**。
4. **后端 PBKDF2-HMAC-SHA256 加盐哈希与令牌自动轮换 (`Cryptographic Storage & Token Rotation`)**：
   - 密码存储采用 `hashlib.pbkdf2_hmac('sha256', raw_pw, salt, 10000)` + `hmac.compare_digest` 恒定时间比对；每次修改或重置密码时自动生成新随机盐值并轮换 `token_secret`，使旧会话令牌立即失效。

---

## 三、 五表 RBAC 数据库模型与字段规格设计 (`PostgreSQL 18 + SQLite WAL` 14表同构)

平台数据库由原 9 张业务与高可用表扩展为 **14 张受治关系表**，其中 **5 张为 RBAC 权限管理核心表**（DDL 定义于 [V005__complete_portable_schema.sql](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/db_migrations/V005__complete_portable_schema.sql)）：

### 1. `sys_users`（系统用户与认证凭证主表 — `PK: user_id`, `UK: username`）
| 字段名 (`Column`) | 数据类型 (`PG18 / SQLite`) | 约束与默认值 | 字段业务与安全职责说明 |
| :--- | :--- | :--- | :--- |
| `user_id` | `VARCHAR(64)` | `PRIMARY KEY` | 用户唯一主键标识（如 `admin`, `colleague_a`） |
| `username` | `VARCHAR(64)` | `UNIQUE NOT NULL` | 登录账号名（唯一索引 `idx_users_username`） |
| `display_name` | `VARCHAR(128)` | `NOT NULL` | 界面展示名称 |
| `role` | `VARCHAR(32)` | `NOT NULL DEFAULT 'SCHOLAR'` | 绑定角色编码（`ADMIN` 管理员 / `SCHOLAR` 普通用户） |
| `account_status` | `VARCHAR(32)` | `NOT NULL DEFAULT 'ACTIVE'` | 账号状态（`ACTIVE` 正常 / `DISABLED` 管理员停用阻断登录） |
| `passcode_hash` | `VARCHAR(128)` | `NOT NULL` | `PBKDF2-HMAC-SHA256` (10,000次迭代) 64位十六进制密码哈希 |
| `passcode_salt` | `VARCHAR(64)` | `NOT NULL` | 每用户独立随机盐值（改密/重置时自动重新生成） |
| `token_secret` | `VARCHAR(128)` | `NOT NULL` | Bearer 会话签名令牌（改密/重置密码后自动轮换吊销旧会话） |
| `failed_login_count` | `INTEGER` | `NOT NULL DEFAULT 0` | 连续密码错误次数统计（登录成功后清零） |
| `last_login_at` | `VARCHAR(64)` | `NOT NULL DEFAULT ''` | 最近一次成功登录时间戳 |
| `password_updated_at`| `VARCHAR(64)` | `NOT NULL DEFAULT ''` | 最近一次密码修改或管理员重置时间戳 |
| `created_by` | `VARCHAR(64)` | `NOT NULL DEFAULT 'system'` | 创建该账号的操作人 `user_id` |
| `created_at` | `VARCHAR(64)` | `NOT NULL` | 账号创建时间戳 |

### 2. `sys_roles`（RBAC 角色层级定义表 — `PK: role_code`）
| 字段名 (`Column`) | 数据类型 | 约束与默认值 | 字段说明与预置数据 |
| :--- | :--- | :--- | :--- |
| `role_code` | `VARCHAR(32)` | `PRIMARY KEY` | 角色编码：`ADMIN` / `SCHOLAR` / `GUEST` |
| `role_name` | `VARCHAR(64)` | `NOT NULL` | 角色名称：系统管理员 / 正式研友学籍 / 未登录访客 |
| `role_level` | `INTEGER` | `NOT NULL DEFAULT 50` | 权限等级：`ADMIN=100`, `SCHOLAR=50`, `GUEST=10` |
| `is_system` | `INTEGER` | `NOT NULL DEFAULT 1` | 系统内置角色保护标志（`1=不可物理删除`） |
| `description` | `TEXT` | `NOT NULL DEFAULT ''` | 角色权责边界说明 |
| `created_at` | `VARCHAR(64)` | `NOT NULL` | 创建时间戳 |

### 3. `sys_permissions`（RBAC 原子权限点注册表 — `PK: perm_code`）
| 字段名 (`Column`) | 数据类型 | 约束与默认值 | 字段说明（共预置 11 项原子权限点） |
| :--- | :--- | :--- | :--- |
| `perm_code` | `VARCHAR(64)` | `PRIMARY KEY` | 原子权限码（如 `account:password:self`, `admin:user:create`, `admin:user:password_reset`） |
| `perm_name` | `VARCHAR(128)` | `NOT NULL` | 权限中文名称 |
| `resource_domain` | `VARCHAR(64)` | `NOT NULL` | 资源域（`PASSAGE` / `VOCAB` / `ESSAY` / `INGEST` / `ACCOUNT` / `RBAC_ADMIN`） |
| `action_type` | `VARCHAR(32)` | `NOT NULL` | 操作类型（`READ` / `WRITE` / `MANAGE` / `AUDIT`） |
| `description` | `TEXT` | `NOT NULL DEFAULT ''` | 权限点详细定义 |

### 4. `sys_role_permissions`（角色-权限多对多授权映射表 — `PK: (role_code, perm_code)`）
| 字段名 (`Column`) | 数据类型 | 约束与默认值 | 角色授权矩阵映射关系 |
| :--- | :--- | :--- | :--- |
| `role_code` | `VARCHAR(32)` | `PK Component` | `GUEST` (1项) / `SCHOLAR` (6项) / `ADMIN` (全量11项) |
| `perm_code` | `VARCHAR(64)` | `PK Component` | 关联 `sys_permissions.perm_code` |
| `granted_at` | `VARCHAR(64)` | `NOT NULL` | 授权时间戳 |
| `granted_by` | `VARCHAR(64)` | `NOT NULL DEFAULT 'system'` | 授权操作人 |

### 5. `sys_rbac_audit_log`（RBAC 安全审计流水表 — `PK: audit_id`）
| 字段名 (`Column`) | 数据类型 | 约束与默认值 | 审计追踪说明 |
| :--- | :--- | :--- | :--- |
| `audit_id` | `VARCHAR(64)` | `PRIMARY KEY` | 审计流水唯一主键 (`aud-...`) |
| `actor_user_id` | `VARCHAR(64)` | `NOT NULL` | 执行操作的用户 ID |
| `actor_role` | `VARCHAR(32)` | `NOT NULL` | 操作人当时角色 (`ADMIN` / `SCHOLAR` / `GUEST`) |
| `target_user_id` | `VARCHAR(64)` | `NOT NULL` | 被操作的目标账号或受保护接口路径 |
| `action` | `VARCHAR(64)` | `NOT NULL` | 事件枚举 (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `SELF_PASSWORD_CHANGE`, `ADMIN_USER_CREATE`, `ADMIN_PASSWORD_RESET`, `ADMIN_ROLE_STATUS_CHANGE`, `UNAUTHORIZED_BLOCKED`) |
| `detail_json` | `TEXT` | `NOT NULL DEFAULT '{}'` | 脱敏审计上下文 JSON（严禁记录明文口令） |
| `client_ip` | `VARCHAR(64)` | `NOT NULL DEFAULT '127.0.0.1'`| 客户端来源 IP |
| `created_at` | `VARCHAR(64)` | `NOT NULL` | 事件发生时间戳 |

---

## 四、 登录后专题账号管理系统功能矩阵与 38/38 零 Bug 验收报告 (`ev:ev-0014`)

### 1. 角色权责与专题界面 (`#tab6` 账号与 RBAC 管理中心) 隔离矩阵

| 功能模块 / API 端点 | 未登录访客 (`GUEST` L10) | 普通用户 (`SCHOLAR` L50) | 系统管理员 (`ADMIN` L100) |
| :--- | :---: | :---: | :---: |
| **顶栏『账号与RBAC管理』Tab 入口 (`#tabBtn6`)** | 🔒 隐藏不可见 | ✅ 显示 `🔐 5. 账号与密码管理 (本人)` | ✅ 显示 `🛡️ 5. 账号与RBAC管理 (ADMIN)` |
| **查看本人角色、已授权限与五表 Schema (`GET /api/auth/me`)** | 返回 `GUEST` | ✅ 允许 (`6` 项本人读写权限) | ✅ 允许 (`11` 项全量权限) |
| **修改本人登录密码 (`POST /api/auth/password/change`)** | ⛔ `401` 拦截 | ✅ 允许（需校验本人原密码） | ✅ 允许（需校验本人原密码） |
| **修改他人登录密码 (`POST /api/auth/password/change` 跨账号)** | ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 可通过管理员重置接口执行 |
| **查看全量注册账号脱敏台账 (`GET /api/admin/users`)** | ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 允许（密码列脱敏为 `••••••••`） |
| **手工新增普通用户或管理员 (`POST /api/admin/users`)** | ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 允许（支持选 `SCHOLAR` 或 `ADMIN`） |
| **强制重置任意账号密码 (`POST /api/admin/users/password`)** | ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 允许（自动轮换目标账号 Token） |
| **切换账号角色与启停状态 (`POST /api/admin/users/role_status`)**| ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 允许（含管理员防自锁 `422` 保护） |
| **查阅 RBAC 安全审计流水 (`GET /api/admin/rbac/audit`)** | ⛔ `401` 拦截 | ⛔ **`403 Forbidden` 刚性拦截** | ✅ 允许（实时展示最近 40 条安全流水） |

### 2. 生产真机 38/38 全量测试验收清单 (`ev:ev-0014` · `0 Bug`)

| 测试批次与编号 | 测试维度与验收用例描述 | 预期结果 | 实测结果 |
| :--- | :--- | :--- | :---: |
| **`STATIC-01 ~ 08`** | 未登录 30%/45%/25% 分级披露、毛玻璃遮罩、服务端 `GUEST_TEASER` 截断 | `8/8 PASS` | ✅ **PASS** |
| **`STATIC-09 ~ 18`** | `BUG-01 ~ BUG-10` 全部按钮高亮同步、词库排序解析、批量 CSV 导词修复 | `10/10 PASS` | ✅ **PASS** |
| **`STATIC-19 ~ 26`** | `RBAC-01 ~ RBAC-08` 页面零明文口令、6处密码框掩码反记忆、5张RBAC表、PBKDF2、防自锁 | `8/8 PASS` | ✅ **PASS** |
| **`E2E-01` (线上 HTML)** | 线上 `GET /` 检查零明文口令 (`kaoyan2026`/`Kaoyan@Admin2026` 均不存在) 且含掩码属性 | `HTTP 200` | ✅ **PASS** |
| **`E2E-02` (14表健康度)** | 线上 `GET /api/health` 校验 `tables_count == 14`，包含全部 5 张 RBAC 表 | `14 Tables OK` | ✅ **PASS** |
| **`E2E-03` (访客沙箱)** | 未登录 `GET /api/auth/me` 返回 `GUEST`，`GET /api/state` 返回 `GUEST_TEASER` | `HTTP 200` | ✅ **PASS** |
| **`E2E-04` (访客拦截)** | 未登录直接请求 `GET /api/admin/users` 与 `POST /api/admin/users/password` | 刚性拦截 `401` | ✅ **PASS** |
| **`E2E-05` (普通用户登录)**| `colleague_a` / `kaoyan2026` 登录返回 `role="SCHOLAR"` 与 6 项普通权限 | `HTTP 200` | ✅ **PASS** |
| **`E2E-06` (普通用户越权)**| `colleague_a` 携带 Token 请求 4 个 `/api/admin/*` 接口全部被 `require_admin` 阻断 | 刚性拦截 `403` | ✅ **PASS** |
| **`E2E-07` (跨账号改密拦截)**| `colleague_a` 尝试修改 `scholar_b` 的密码被阻断并写入 `UNAUTHORIZED_BLOCKED` 审计 | 刚性拦截 `403` | ✅ **PASS** |
| **`E2E-08` (本人改密闭环)**| `colleague_a` 修改本人密码为临时新密码再恢复为原密码，验证 Token 自动轮换 | `HTTP 200` | ✅ **PASS** |
| **`E2E-09` (管理员登录)** | `admin` / `Kaoyan@Admin2026` 登录返回 `role="ADMIN"` 与全部 11 项权限 | `HTTP 200` | ✅ **PASS** |
| **`E2E-10` (脱敏台账查询)**| `admin` 调用 `GET /api/admin/users`，全部用户密码显示 `••••••••` 且无哈希泄露 | `HTTP 200` | ✅ **PASS** |
| **`E2E-11` (建号/重置/启停)**| `admin` 创建 `scholar_c`、强制重置其密码、将其设为 `DISABLED` 验证禁止登录(`403`)后再恢复 `ACTIVE` | 全链路 `200/403` | ✅ **PASS** |
| **`E2E-12` (管理员防自锁)**| `admin` 尝试将自身账号降级为 `SCHOLAR` 或设为 `DISABLED` 触发防自锁保护 | 拦截 `422` | ✅ **PASS** |
