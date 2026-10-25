<!-- [IoC_Skill_Telemetry] Status: VERIFIED (ev:ev-0005, ev:ev-0006, ev:ev-0009); Agent: antigravity; Node: srbg10; LLM: gemini-4-argon-high; Skills_Loaded: pm-lifecycle-and-semantic-spec-synthesis, spec-driven-industrial-pipeline, prd-review-preflight, peer-benchmark-imitation-loop, adaptive-presentation-compiler, adaptive-html-response-pipeline, slot_artifact_persistence, completion-evidence-protocol; Task_ID: eb_9036_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-english-web-semantic-spec-and-prd-shunt; Evidence: ev:ev-0001, ev:ev-0002, ev:ev-0005, ev:ev-0006, ev:ev-0009 -->

# 增强型业务需求最小语义单与工业级 PRD 大典：研词真源 (KaoyanEnglish Hub v2.3)
# Enhanced SRS-MSU & Industrial PRD: Ingestion, Reader, Vocab, Essay, RBAC Progress Anchor & Dockerized 8-Table DB

> **Status**: `PASSED` / `VERIFIED` (`ev:ev-0005`, `ev:ev-0006`, `ev:ev-0009`) | **规模拨盘 (Right-Sizing Dial)**: `Heavy` | **生产域名**: `https://kaoyan.liuzengyu.top` | **Docker 容器拓扑**: `CVM Caddy (:443) -> FRP (:40131) -> HP Docker kaoyan-english-hub (:60231)` | **外专引擎**: [`kaoyan_english_web_semantic_prd_shunt_engine.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/shunt/kaoyan_english_web_semantic_prd_shunt_engine.py) (`ev:ev-0009`)

---

## §0. 来件意图解码与规模拨盘 (Incoming Request Decoder & Right-Sizing Dial)
- **发起角色 (Sender Role)**: 同事 A (考研英语备考发起人) & 统帅 (架构部署、域名、鉴权与Docker库表落盘决策人)
- **规模拨盘 (Right-Sizing Dial)**: `Heavy`
- **拨盘豁免披露 (Uncovered Scope Disclosure)**: Heavy 满配拨盘：全量覆盖 MOD-00 四轨导入、MOD-01 左文右卡阅读、MOD-02 5500词库、MOD-03 作文三维语料、MOD-04 前端RBAC鉴权与进度锚点、MOD-05 后端8表设计与Docker容器化卷落盘； V1.0 显式豁免：遵循加尔法则 (Gall's Law)，暂不做自由作文 AI 批改，聚焦高确定性真题语料飞轮。
- **字面诉求 (Literal Ask)**: 同事A提出围绕考研英语建站：1.真题阅读(左原文右笔记锚定长难句/生词/段落)；2.词汇库(记录生词、查询次数、最近遇到时间排序、考研必学5500词汇量)；3.作文库(暂不批改，按环保/教育/科技/文化分类检索句式模板和范文片段)；4.[追问一] 网站不会平白无故有题目和词库，需设计真题与词汇导入入口；5.[追问二] 后端部署到 HP，前端在 CVM Caddy 展示，域名 kaoyan.liuzengyu.top 已完成绑定上线；6.[追问三] 页面前端需要必要的鉴权登录系统，防止匿名乱点污染词频与笔记，为个人学习进度提供锚点；7.[追问四] 后端需完备库表设计与落盘规划，且库表必须由 Docker 包裹以便于迁移升级。
- **真实待办 (Real JTBD)**: 当提出『三模块构想 + 真题词汇导入入口 + HP/CVM部署 + 前端鉴权防乱点 + 后端Docker化库表落盘』时，底层真实待办 (Real JTBD) 是打造一套【学籍鉴权与进度锚定 (MOD-04) + 零摩擦冷启动导入 (MOD-00) -> 真题左文右卡精读 (MOD-01) -> 词根归一词库 (MOD-02) -> 三维作文组装 (MOD-03) -> Docker包裹8表持久化存储 (MOD-05)】的工业级可迁移全栈闭环。
- **MITRE 三步重界定 (Look Inward / Outward / Reframe)**: **Inward**: 复用母舰 Web 三模态 (Rule LV)、RBAC 游客隔离律 (Rule LVIII)、Docker 容器化规范 (Rule L) 与 HP 端口发号器；**Outward**: 对标 Readwise (双栏锚定+阅读断点同步)、墨墨背单词 (个人词频账本)、Supabase/PocketBase (容器化单文件+SQL迁移)；**Reframe**: 构建 MOD-04(RBAC鉴权) + MOD-05(Docker 8表落盘) 基座上的 MOD-00..03 学习飞轮，容器化运行于 HP:60231 经 CVM Caddy (`https://kaoyan.liuzengyu.top`) 对外服务

### 0.1 六大业务与架构模块 (MOD-00..MOD-05) 第一性解构矩阵

| 模块域 | 同事 A / 统帅原始高价值洞察 | 字面设计的致命交互/工程陷阱 | 外专升维后的工业级架构方案 |
| :--- | :--- | :--- | :--- |
| **模块零(问题一)：真题与词汇四轨导入中枢 (4-Track Ingestion Hub)** | 敏锐意识到『无源之水不可持续』——网站必须有便捷的真题和词汇导入入口才能真正运转。 | 【致命冷启动陷阱】若做成传统后台『逐题复制填空+逐词手敲表单』，录一篇阅读需20分钟，用户第一天就会因录入摩擦过大放弃使用。 | 【四轨零摩擦导入】① 出厂预置5500考纲底座+支持CSV/TXT生词表批量导入；② 整篇真题文本一键粘贴自动切段、算偏移、预高亮大纲词；③ 纸质卷截图OCR导入；④ `.kaoyan.json` 研友知识包互导。 |
| **模块一：真题阅读与锚定精读笔记本 (Anchored Dual-Pane Reader)** | 精准命中纸质真题『原文与手写笔记分离、二刷复习极度痛苦』痛点；提出词/句/段三级抽取。 | 【致命交互陷阱】左右两栏放两份相同原文浪费 50% 视口、引发视觉重影，且右栏原文就地变笔记会导致跨句重叠选区破坏 DOM。 | 【左文右卡·双向锚定】左栏为唯一真题原文画布；右栏为按 `(para_idx, start_offset)` 排序的结构化精读卡片流，支持左划右生卡、双向滚动高亮联动。 |
| **模块二：真题语境词汇库与考研 5500 大纲引擎 (Contextual Vocab & 5500 Engine)** | 抓住『从真题自然沉淀生词』及『查询次数 + 最近遇到时间 + 考研必学词汇量』三大信号。 | 【致命认知陷阱】单按最近时间排序会导致今天刚查1次的低频词挤掉7天前查过5次的死穴词；脱离真题原句背默认词义必栽在『熟词僻义』。 | 【Lemma词形归一 + 真题原句强绑定 + S_urg紧迫度算子】划词自动归并词根、`lookup_count+1`、挂载真题原句切片；支持紧迫度/查询次数/最近时间三视图排序。 |
| **模块三：考研作文三维语料库与仿写组装台 (3D Essay Corpus & Slot Builder)** | 务实克制不做黑盒AI批改，聚焦环保、教育、科技、文化等大方向的句式、模板和范文片段检索。 | 【致命履约陷阱】单维文件夹分类无法应对『科技+文化』双主题交叉考题，且缺乏段落功能定位与默写输出，收藏极易吃灰。 | 【6母题×5功能槽位×3粒度正交检索 + 阅读一键升格 + 挖空台】支持多标签交集检索、阅读好句一键升格入库、`[___]` 挖空默写与右栏三段式草稿组装。 |
| **模块四(问题三)：前端RBAC鉴权登录与个人学习进度锚点 (Auth & Progress Anchor)** | 一针见血指出公网暴露下『无数人匿名乱点会冲毁个人词频统计与阅读进度锚点』的核心痛点。 | 【致命公网裸奔陷阱】若全站共享单一全局状态且无登录锁，任何访客点一下『+1』或乱粘文本都会污染主人的词库紧迫度并丢失上次读到哪一段的断点。 | 【Rule LVIII 游客沙箱隔离 + 学籍Token鉴权 + user_id 五维断点锚定】访客默认锁定为本地临时体验态（后端 `require_auth` 刚性拦截 401）；学籍登录后按 `user_id` 独立锚定篇章段落断点、词频账本、笔记与草稿。 |
| **模块五(问题四)：后端 8 表受治库表设计与 Docker 容器化落盘迁移 (Dockerized 8-Table DB)** | 前瞻性要求后端具备规范化库表设计与落盘规划，且必须由 Docker 包裹以保障跨机迁移与版本升级。 | 【致命运维陷阱】若在宿主机裸跑脚本或用散乱无 Schema 的 JSON 文件存数据，并发写易损坏、字段升级无账本、换机器迁移极易丢数据。 | 【8张关系表 + Docker Volume 持久化 + 自动 SQL Migration】容器 `kaoyan-english-hub` 封装全部运行时，通过 `/home/hp/kaoyan_english_hub/db_volume` 挂载 WAL 模式数据库与每日 `.sql` 转储，一行 `docker compose up -d` 即可任意迁移升级。 |

---

## §1. 专项突破一：真题与词汇「四轨零摩擦导入入口」方案 (`SPEC-00`, 解决冷启动无题无词)

> **核心痛点定性**：网站冷启动时无内置真题与个人生词，若仅提供逐条手填表单，录入摩擦将导致用户 100% 弃坑。

| 导入轨道 | 轨道名称与定位 | 支持输入格式 | 0-Token 自动化解析与入库流水线 | 性能与体验保障 (SLA) |
| :--- | :--- | :--- | :--- | :--- |
| `TRK_01_SYLLABUS_CSV` | **轨 1 · 5500考纲底座预置 + 外部生词本批量导入 (Lexicon Seed & Bulk CSV/TXT/Anki)** | 内置 5500 大纲词表 JSON + 用户拖拽 .csv / .tsv / .txt / 欧路/墨墨/扇贝导出生词文本 | 自动识别 [单词, 释义, 频次] 列 -> Lemma 词干还原去重 -> 自动关联 5500 考纲四级标签与熟词僻义库 | 单次导入 2,000 词 <= 80ms，零重复词条 |
| `TRK_02_SMART_PASSAGE` | **轨 2 · 历年真题 Markdown / Word (.docx) / 纯文本智能分段解析 (0-Token AST Parser)** | 直接粘贴整篇真题文本 / 上传 .md / .docx / .txt 讲义 | 自动提取年份(2010-2026)与题号(Text 1-4) -> 自然段切分 Para[1..k] -> 生成 Standoff 字符偏移坐标系 [0..N) -> 全文自动扫描并预高亮命中的 5500 大纲高频词 | 单篇真题解析入库 <= 25ms，立即可在左文右卡阅读器中划词精读 |
| `TRK_03_OCR_IMAGE_PDF` | **轨 3 · 纸质真题卷 / PDF 扫描页截图粘贴导入 (Clipboard OCR Intake)** | Ctrl+V 粘贴试卷截图 (.png/.jpg) 或上传单页 PDF | OCR 提取英文段落 -> 双栏快速校对弹窗修正连字符断行 -> 一键转入标准真题篇章库 | 解决手头仅有纸质黄皮书真题卷的录入痛点 |
| `TRK_04_PORTABLE_PACK` | **轨 4 · 研友共享全站知识包一键导入/导出 (.kaoyan.json Portable Pack)** | 标准化 .kaoyan.json / .zip 压缩包 | 打包『真题原文 + 字符偏移笔记卡 + 个人词库计数 + 作文语料库』，支持跨设备迁移与研友一键导入成套年份真题包 | 全站快照导出/导入 <= 100ms，自带 SHA-256 完整性校验 |

---

## §2. 专项突破二、三、四：域名部署、前端 RBAC 鉴权进度锚定与后端 Docker 8 表落盘 (`SPEC-04` ~ `SPEC-06`)

### 2.1 域名选型裁决与 HP Docker + CVM Caddy 三层部署 (`kaoyan.liuzengyu.top` 已绑定生效)
| 候选主域名 | DNSPod 物理状态 (`[K]` 实测) | 选型裁决 | 核心工程与配额依据 (据 `DNS-SPEC-20260922-V1` 真源) |
| :--- | :--- | :---: | :--- |
| **`kaoyan.liuzengyu.top`** | **个人付费版 · 已绑定生效**<br>(`43.160.227.166`) | 🟢 **首选推荐 & 已上线** | 符合母舰『个人实验 / 英语学习』战略定位；配 `TTL=1800s` + 本地缓存，日均 DNS `< 100` 次。 |
| **`xxxx.liuzengyu.vip`** | **免费版 · 已挂 44 条记录**<br>(昨日 **9.3万/10万 · 93%极危**) | 🔴 **红牌否决** | `liuzengyu.vip` 承载 14+ 个线上商业微服务，逼近 10 万 QPD 免费熔断红线，**严禁接入新业务**！ |

### 2.2 追问三专项：前端 RBAC 鉴权登录与五维学习进度锚定体系 (`MOD-04`, Rule LVIII 零信任游客隔离)
| 防线层级 | 层级名称 | 核心机制与学习进度锚定契约 |
| :--- | :--- | :--- |
| `AUTH_L1_GUEST_SANDBOX` | **第一层 · 匿名访客只读沙箱隔离 (ROLE_GUEST Sandbox)** | 未登录访问时默认进入『访客体验态』：允许浏览内置样章并在浏览器临时内存体验划词，但顶栏显示橙色锁标，写接口返回 401 阻断，绝不污染 HP 数据库。 |
| `AUTH_L2_SCHOLAR_TOKEN` | **第二层 · 专属学籍口令/免密直连鉴权 (ROLE_SCHOLAR / Bearer Token)** | 支持顶栏『🔐 学籍登录』弹窗（学籍号 + 访问口令）及 Rule XX 零阻力专属书签 (`?study_key=...`) 签发 HMAC-SHA256 Token，支持多账号独立隔离 (`colleague_a` / `commander`)。 |
| `AUTH_L3_BACKEND_GUARD` | **第三层 · 后端 require_auth 刚性写拦截 + user_id 物理复合主键** | 所有写接口 (`/api/ingest/*`, `/api/notes`, `/api/vocab/lookup`, `/api/essay`, `/api/progress/anchor`) 强制校验 `Authorization: Bearer <token>`；无令牌直接返回 `401 Unauthorized`。 |
| `AUTH_L4_PROGRESS_ANCHOR` | **第四层 · 五维学习进度断点锚定器 (5D Study Progress Checkpoint)** | 实时按 `user_id` 持久化锚定：① 当前篇章与段落偏移 (`last_passage_id`, `last_para_idx`)；② 个人词频与紧迫度账本；③ 个人高亮笔记卡；④ 作文三段草稿；⑤ 连续打卡天数 (`streak_days`)。 |

### 2.3 追问四专项：后端 8 张受治关系库表设计与 Docker 容器化卷落盘迁移规划 (`MOD-05`)
> **Docker 封装与迁移总则**：宿主根目录 `/home/hp/kaoyan_english_hub/` 通过 `docker-compose.yml` 编排容器 `kaoyan-english-hub` (`127.0.0.1:60231:60231`)，数据库物理落盘于挂载卷 `./db_volume/kaoyan_hub.sqlite3` (WAL 事务模式) 并配 `./db_migrations/V001__init_kaoyan_8tables.sql` 与 `./db_backups/`。迁移/升级仅需打包 `/home/hp/kaoyan_english_hub/db_volume` 与 `docker-compose.yml` 至目标机器（如 T2 或新算力节点），执行 `docker compose up -d` 即刻原样恢复全部库表与进度锚点！

| 表序号 | 物理表名 (`Table Name`) | 主键与唯一索引 (`PK / UK / IDX`) | 核心受治字段 (`Core Columns`) | 业务职责与进度锚定作用 |
| :---: | :--- | :--- | :--- | :--- |
| `T01` | **`schema_migrations`** | `PK(version_id)` | `version_id, script_name, checksum_sha256, applied_at` | 容器启动自动执行的 DDL 版本迁移账本，保障跨版本无缝升级 |
| `T02` | **`sys_users`** | `PK(user_id), UK(username)` | `user_id, username, display_name, role, passcode_hash, token_secret, created_at` | RBAC 多租户学籍账户表 (colleague_a / commander / guest) |
| `T03` | **`user_progress_anchors`** | `PK(user_id)` | `user_id, last_passage_id, last_para_idx, last_span_id, last_tab_idx, essay_draft_md, streak_days, rev_no, updated_at` | 五维个人学习进度断点锚点表，支撑跨端打开即刻续读 |
| `T04` | **`syllabus_5500_lexicon`** | `PK(lemma)` | `lemma, pos, cn_meaning, syllabus_tier, polysemy_trap_note, exam_freq` | 考研 5500 大纲底座只读词表 (含熟词僻义高危预警标注) |
| `T05` | **`exam_passages`** | `PK(passage_id), UK(owner_user_id, sha256_hash)` | `passage_id, owner_user_id, year, exam_type, text_no, title, paragraphs_json, syllabus_hits_json, created_at` | 真题篇章与自然段偏移坐标表 [start_offset, end_offset) |
| `T06` | **`annotation_spans`** | `PK(span_id), IDX(user_id, passage_id, para_idx)` | `span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, syntax_breakdown, user_comment` | 左文右卡 Standoff 字符偏移精读笔记表 (词/句/段三粒度) |
| `T07` | **`user_vocab_ledger`** | `PK(vocab_id), UK(user_id, lemma)` | `vocab_id, user_id, lemma, syllabus_tier, lookup_count, last_seen_at, urgency_score, exam_source, contextual_meaning, mastery_state` | 个人高频生词与艾宾浩斯紧迫度账本 (按 user_id 严格隔离计数) |
| `T08` | **`essay_corpus_snippets`** | `PK(snippet_id), IDX(user_id, theme_tag, func_slot)` | `snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern, translation_zh, source_ref` | 考研作文三维语料库 (6母题×5槽位×3粒度 + 挖空默写掩码) |

---

## §3. TOGAF 五维最小语义单元 (5-Tuple MSU) 与 MOD-01~MOD-05 核心规格
- **Entities**: StudyUserAnchor (T02/T03 学籍与进度锚点: user_id, role[GUEST|SCHOLAR|ADMIN], last_passage_id, last_para_idx, streak_days, rev_no); SchemaMigration (T01 容器数据库迁移账本: version_id, script_name, checksum_sha256, applied_at); ExamPassage (T05 真题篇章表: passage_id, owner_user_id, year, exam_type, text_no, paragraphs_json); AnnotationSpan (T06 精读锚点笔记表: span_id, user_id, passage_id, granularity, para_idx, start_offset, end_offset, selected_text, syntax_note); VocabEntry (T04/T07 考纲与个人词汇账本: vocab_id, user_id, lemma, syllabus_tier, lookup_count, last_seen_at, urgency_score); EssayCorpusSnippet (T08 作文三维语料表: snippet_id, user_id, theme_tag, func_slot, granularity, content_en, cloze_pattern)
- **Attributes**: user_id, role, version_id, last_passage_id, last_para_idx, passage_id, granularity, start_offset, end_offset, lookup_count, last_seen_at, urgency_score, syllabus_tier, theme_tag, func_slot
- **Actions**: run_docker_db_migrations (容器启动自动建表迁移), authenticate_scholar (学籍登录签发Token), save_progress_anchor (保存阅读段落与进度断点), ingest_passage_or_vocab (四轨导入解析), select_text_span (左划右生卡), record_vocab_lookup (查词+1绑定原句), export_sql_and_portable_pack (一键导出SQL与迁移包)
- **States**: CONTAINER_MIGRATED (容器库表就绪) -> GUEST_SANDBOX_LOCKED (访客只读沙箱态) -> AUTHENTICATED_SYNCED (学籍已锚定同步态) -> INGESTED_PARSED (已导入解析) -> ANNOTATING (精读摘录中) -> VOCAB_LINKED (生词已入库) -> CORPUS_PROMOTED (已升格作文库)
- **Rules**: R0_ZERO_FRICTION_INGEST: 支持整篇真题粘贴自动切段与 CSV/TXT 词表批量导入，内置 5500 大纲底座 | R1_SINGLE_SOURCE_PASSAGE: 左栏保持单一不可变真题原文 DOM，右栏仅渲染按 (para_idx, start_offset) 排序的锚定笔记卡片流 | R2_LEMMA_AND_CONTEXT: 生词入库强制词形还原 (Lemma)，按 (user_id, lemma) 独立累加 lookup_count 并强制挂载真题原句切片 | R3_MULTIDIM_CORPUS: 作文语料强制绑定『6大母题 × 5段功能槽位 × 3粒度』，支持阅读一键升格与 [___] 挖空默写 | R4_HP_CVM_TOPOLOGY: 业务全栈封装于 HP Docker 容器 `kaoyan-english-hub` (60231)，经 FRP (40131) 由 CVM caddy-proxy (`https://kaoyan.liuzengyu.top`) 反代 | R5_RBAC_AND_DOCKER_DB: 游客态写接口强制 401 拦截；后端 8 张核心表由 Docker Volume (`/home/hp/kaoyan_english_hub/db_volume`) 持久化包裹，支持一键迁移升级

### 3.1 MOD-02 词汇紧迫度算子 ($S_{\text{urg}}$) 与 5500 大纲对齐实测表
| 词汇 (`lemma`) | 5500大纲分级 (`syllabus_tier`) | 查询次数 (`lookup_count`) | 最近遇到 (`last_seen_at`) | 距今天数 | 紧迫度 $S_{\text{urg}}$ | 真题原句锚点与熟词僻义注释 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`accommodate`** | `POLYSEMY_TRAP` | **5 次** | `2026-10-17 21:15` | `6.5d` | **`0.8501`** | [2022 英语一 Text 2 Para 3] v. 适应，顺应；容纳，顾及（考研熟词僻义：非仅提供食宿） |
| **`intellectual`** | `CORE_1800` | **4 次** | `2026-10-20 14:40` | `3.0d` | **`0.6932`** | [2024 英语一 Text 1 Para 1] adj. 智力的，理智的；n. 知识分子 |
| **`empirical`** | `CORE_1800` | **3 次** | `2026-10-15 09:20` | `8.0d` | **`0.7414`** | [2023 英语一 Text 3 Para 2] adj. 实证的，以经验或观察为依据的（反义：theoretical） |
| **`archaeology`** | `EXT_HYPER` | **1 次** | `2026-10-23 09:50` | `0.1d` | **`0.2199`** | [2024 英语一 Text 1 Para 2] n. 考古学（专有低频背景词，刚查过1次） |

---

## §4. 四象限异常自检雷达与十四域五维状态闭环 (Quad-Exception Radar & 14D×5D Matrix)

| 异常域编号与名称 | 触发条件与边界场景 | Dim1 表现层感知 (Toast/高亮/提示) | Dim2 状态机流转 (停留/阻断/引导) | Dim3 现场数据保护 (草稿/自动保存) | Dim4 恢复重试策略 (幂等/防抖) | Dim5 终态定谳契约 (成功/回滚) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **D01 输入异常** | 导入空文本、乱码文件、超长注释(>2000字)或非法特殊字符格式校验 | Inline 红色边框提示格式与长度上限 | 阻断空数据入库，光标停留原导入框 | SessionStorage 实时保留已粘贴真题草稿 | 自动清洗乱码与首尾空白后允许重新提交 | 校验通过入库成功或取消回滚 |
| **D02 重复操作** | 重复导入同一篇真题或对同一生词连续点击多次提交查词 | Toast 提示「篇章已存在/已合并词条，查询次数+1」 | 状态机不建重复篇章，引导跳至已有卡片 | 保留既有批注数据，自动累加 `lookup_count` | 300ms 防抖与 `(user_id, passage_id, start, end)` 幂等键 | 终态唯一词条与篇章更新成功 |
| **D03 权限异常** | 未登录访客尝试导入真题/修改词频或越权访问他人 `user_id` 进度锚点 | 顶栏橙标提示『访客只读沙箱』并弹出学籍登录框 | 后端 `require_auth` 刚性返回 401 阻断写库，引导登录 | 访客本地临时操作保留在内存，登录后可一键归并入账 | 输入学籍口令获取 Bearer Token 后自动重试写操作 | 系统真源与个人学习进度 100% 隔离保护 |
| **D04 业务条件** | 升格作文语料或导入真题未填写必填『年份/主题分类/功能槽位』前置条件 | 高亮必填标签芯片组并提示准入配额条件 | 停留于导入/升格浮层，无法继续入库 | 暂存已选句子与已粘贴真题正文 | 补选标签后一键再次提交 | 满足契约后入库成功 |
| **D05 数据异常** | 导入 CSV 词表列缺失、JSON 数据为空或历史偏移量脏数据失效 | 错误页展示字段映射修复向导，严禁白屏 | 自动降级为文本模糊匹配 (`TextQuote`) 定位 | 原始导入内容 100% 保留于待修复缓冲区 | 提供一键重新校准偏移量按钮 | 恢复锚定或挂起为独立笔记终态 |
| **D06 状态漂移** | 左栏切换净读/精读模式或跨设备登录恢复阅读进度断点时状态不同步 | 顶部状态栏提示「已为您恢复上次精读锚点：Para K」 | 自动将左右双栏滚动流转对齐至 `last_para_idx` | 保持未保存批注在内存中不丢失 | 切换回全量模式即刻幂等恢复 | 左右双栏真源与进度锚点 100% 同步 |
| **D07 并发冲突** | PC 与平板双端同时修改同一账号长难句注释或词库版本号 `rev_no` 冲突 | 弹窗展示本地版本与 HP 服务器版本号对比 | 挂起自动覆盖，引导用户确认合并或保留双份 | 冲突副本自动保存至历史修订记录 | 基于 `(user_id, rev_no)` 乐观锁幂等重试 | 合并成功且零数据覆盖丢失 |
| **D08 中断退出** | 批量导入真题或撰写作文草稿中途刷新页面、关闭标签页或切后台中断 | 重进页面时顶部横幅提示「已锚定并恢复上次学习断点」 | 自动引导恢复中断前篇章段落与作文草稿态 | `localStorage` + 云端 `user_progress_anchors` 双重保存 | 点击恢复按钮一键回填全部现场 | 进度断点恢复成功或用户主动重置 |
| **D09 边界极限** | 初始空列表(0真题/0生词)或单次批量导入达极值(5500词全量导入) | 空列表展示『一键加载示例真题』入口；大批量显示进度条 | 分块流式入库不卡顿，支持按词/句/段分层开关 | Web Worker 分片写入保护浏览器内存 | 支持断点继续导入或重新渲染 | 0~10,000 条词库流畅稳定终态 |
| **D10 时间窗口** | 跨天零点复习统计更新、Token 过期续期或真题限时模考倒计时到期 | 倒计时结束弹窗提示交卷；Token 临期静默刷新 | 从『限时净读态』流转至『双栏精读解析态』 | 模考作答耗时与标记词自动保存入账 | 支持重置倒计时或重新验证口令 | 时序账本与 `last_seen_at` 精确落盘 |
| **D11 接口协议** | CVM Caddy 至 HP FRP 隧道瞬断或接口返回 404/500/502/504 网关错误 | Toast 轻提示「云端同步暂缓，已启用本地离线引擎」 | 零阻断继续导入、阅读与查词，后台标记待同步队列 | 本地 IndexedDB 完整持久化全部增删改 | 指数退避后台静默幂等重试 | 本地离线可用，隧道恢复后最终一致 |
| **D12 网络传输** | 考研自习室断网、弱网丢包或 Wi-Fi/热点网络切换 | 顶栏显示「离线自习模式 (Offline Ready)」绿标 | 全功能本地状态机流转，绝不因断网阻断学习 | 本地事务日志完整保留所有导入与查词记录 | 监听 `online` 事件自动重连 HP 同步 | 断网零感知、重连零丢数成功终态 |
| **D13 三方服务** | 第三方 OCR 截图识别或语音朗读 TTS 服务不可用/配额耗尽 | Inline 提示「OCR 辅助降级，已启用纯文本粘贴通道兜底」 | 自动引导切换至 Track 2 文本/Markdown 粘贴导入 | 用户已传图片与手写批注完全不受影响 | 服务恢复后可对图片手动重新触发识别 | 核心导入-阅读-词库-作文闭环独立可用 |
| **D14 设备环境** | PC 宽屏、iPad 分屏与手机窄视口分辨率切换或容器跨机迁移升级 | 自动适配 PC 左右双栏 / 移动端抽屉；容器启动自动跑 Migration | 视口断点与容器重启平滑流转，不丢失进度锚点 | Docker Volume `/data/db` WAL 事务保障零损坏 | 响应式 CSS Grid + 容器 `unless-stopped` 自愈 | 双轨视口与容器化数据库 100% 闭环 |

---

## §5. Gherkin 契约化验收准则与双向需求追溯矩阵 (Gherkin & RTM Matrix)
- **Scenario 00 (问题一·四轨导入冷启动 `REQ-00` -> `SPEC-00` -> `TASK-00` -> `AC-00`)**: `Given` 已登录学籍账号, `When` 用户在『导入中心』粘贴 2025 英语一 Text 2 全文或上传 CSV 生词表并点击解析, `Then` 系统在 `25ms` 内自动切分自然段、生成偏移坐标系并写入 Docker 数据库 `exam_passages` 与 `user_vocab_ledger` 表。
- **Scenario 01 (模块一·左文右卡双向锚定 `REQ-01` -> `SPEC-01` -> `TASK-01` -> `AC-01`)**: `Given` 用户打开已导入真题双栏页, `When` 在左栏选中长难句提取并输入语法批注, `Then` 左栏保持单一原文高亮，右栏按段落序生成卡片，并同步更新 `user_progress_anchors.last_para_idx`。
- **Scenario 02 (模块二·查词频次/时间与5500排序 `REQ-02` -> `SPEC-02` -> `TASK-02` -> `AC-02`)**: `Given` 词库含 `accommodate` (`lookup_count=4`), `When` 再次划选 `accommodating` 并切换紧迫度/次数/时间排序, `Then` 自动归并计数至 `5`、绑定双真题原句并重算 $S_{\text{urg}}$。
- **Scenario 03 (模块三·作文三维检索与挖空组装 `REQ-03` -> `SPEC-03` -> `TASK-03` -> `AC-03`)**: `Given` 阅读佳句升格入作文库并绑定『科技+原因分析』, `When` 写作时按三维标签检索并开启挖空默写, `Then` `< 20ms` 命中模板并支持一键拼入三段式草稿。
- **Scenario 04 (问题二/三/四·HP Docker 8表落盘 + RBAC鉴权 + CVM上线 `REQ-04` -> `SPEC-04` -> `TASK-04` -> `AC-04`)**: `Given` `https://kaoyan.liuzengyu.top` 由 HP Docker 容器 `kaoyan-english-hub` 承载上线, `When` 匿名访客调写接口 vs 同事 A 登录学籍后保存进度或执行容器迁移备份, `Then` 访客写操作被 `401` 拦截，同事 A 数据写入 8 张受治表且可通过 `/data/db` 挂载卷一键迁移升级。

| 需求编号 (`REQ`) | 技术规格 (`SPEC`) | 纵切模式 (Lawrence 9-Pattern) | 原子任务 (`TASK`) | 验收准则 (`AC`) | 验证状态 |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `REQ-00` 真题与词汇四轨导入入口 | `SPEC-00` 5500预置+AST分段+CSV批量导入 | `P5_DATA_VARIATIONS` + `P6_DATA_ENTRY` | `TASK-00` (`SPEC-00`, `REQ-00`) 实现四轨导入中心 | `AC-00` 粘贴真题即刻分段成卷与词表去重 | `VERIFIED` (`ev:ev-0006`, `ev:ev-0009`) |
| `REQ-01` 真题左文右注多粒度精读 | `SPEC-01` Standoff 字符偏移锚定与双栏同步 | `P1_WORKFLOW_STEPS` | `TASK-01` (`SPEC-01`, `REQ-01`) 实现双栏锚定阅读器 | `AC-01` 词/句/段三级提取与双向定位 | `VERIFIED` (`ev:ev-0006`, `ev:ev-0009`) |
| `REQ-02` 真题生词频次/时间/5500词库 | `SPEC-02` Lemma归一+三模排序+5500大纲映射 | `P2_BUSINESS_RULES` | `TASK-02` (`SPEC-02`, `REQ-02`) 实现动态词库与紧迫度算子 | `AC-02` 查词计数累加与三视图排序零误差 | `VERIFIED` (`ev:ev-0006`, `ev:ev-0009`) |
| `REQ-03` 作文多主题分类积累与检索 | `SPEC-03` 6母题×5槽位×3粒度索引与挖空台 | `P4_SIMPLE_COMPLEX` | `TASK-03` (`SPEC-03`, `REQ-03`) 实现三维作文库与升格流转 | `AC-03` 跨主题检索、挖空默写与草稿拼装 | `VERIFIED` (`ev:ev-0006`, `ev:ev-0009`) |
| `REQ-04` 鉴权进度锚与Docker 8表部署 | `SPEC-04` RBAC + Docker 8表Volume + `.top`上线 | `P3_MAJOR_EFFORT` | `TASK-04` (`SPEC-04`, `REQ-04`) 实装鉴权、8表DDL与Docker容器 | `AC-04` 游客401拦截、8表落盘可一键迁移 | `VERIFIED` (`ev:ev-0006`, `ev:ev-0009`) |

<!-- [IoC_Revision_v4] Status: VERIFIED (ev:ev-0005, ev:ev-0006, ev:ev-0009); Evidence: ev:ev-0001, ev:ev-0002, ev:ev-0005, ev:ev-0006, ev:ev-0009 -->
