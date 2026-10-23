# 研词真源 (KaoyanEnglish Hub v2.4) — 考研英语真题精读·5500词库·三维作文一体化平台

> **Live Demo**: `https://kaoyan.elenalyl.top`
> **Stack**: Zero-Dependency Python 3 HTTP/REST API + SQLite3 WAL (8 Core Tables) + Tri-Modal Single-Page Application (Daylight / Midnight / Eyecare) + Docker Compose + Hot/Warm/Cold Tiered Storage

---

## 1. 核心架构与六大业务模块 (6 Core Modules)

| 模块代号 | 模块名称 | 核心能力 |
| :--- | :--- | :--- |
| **MOD-00** | **四轨内容注入工作台 (Ingestion Studio)** | 支持 JSON/Markdown 真题导入、文章精读实时预览、5500 大纲词入库、三维作文语料实时写库 |
| **MOD-01** | **双栏深度精读器 (Dual-Pane Reader)** | 英文真题原文 + 四色语义高亮 (`vocab`/`grammar`/`discourse`/`translation`) + 段落译文抽屉 + v2 三态减负模式 (`Clean`/`Guided`/`Annotated`) |
| **MOD-02** | **5500 考纲词库与紧急度引擎 (Vocab Engine)** | 紧迫度公式 $S_{\text{urg}} = 0.45 \cdot \ln(1 + F_{\text{exam}}) + 0.35 \cdot (1 - M_u) + 0.20 \cdot \min(1, \Delta t_u / 168)$ 实时重排，支持 SM-2 记忆调度与真题例句溯源 |
| **MOD-03** | **三维作文语料库 (3D Essay Matrix)** | 话题维度 × 功能句型维度 × 逻辑衔接维度三轴正交检索，支持一键加入个人背诵槽与全文背诵遮罩自测 |
| **MOD-04** | **账号鉴权与五维进度锚点 (Auth & Progress)** | 独立注册/登录 (`PBKDF2-HMAC-SHA256` 120,000 次迭代) + 五维断点恢复 (`article_id`, `paragraph_idx`, `scroll_ratio`, `active_tab`, `last_vocab_word`) |
| **MOD-05** | **Docker 8表受治存储与冷热分层 (Tiered Storage)** | 8 张核心 SQLite3 WAL 业务表 + 热数据 (`hot_db`) / 温数据 (`warm_staging`) / 冷归档 (`cold_outbox` Zstandard 压缩异地归档) |

---

## 2. 快速启动 (Quick Start)

### 方式 A：Docker Compose 一键启动（推荐生产环境）

```bash
docker compose up -d --build
curl http://127.0.0.1:60231/api/health
```

### 方式 B：非 Root 普通账号 (`elena`) 宿主机直接运行

```bash
export KAOYAN_PORT=60231
export KAOYAN_DB_PATH=./db_volume/kaoyan_hub.sqlite3
export KAOYAN_MIGRATION_SQL=./db_migrations/V001__init_kaoyan_8tables.sql
export KAOYAN_BACKUP_DIR=./db_backups
python3 kaoyan_hub_server.py
```

---

## 3. 数据库 8 张核心表 (8 Core Tables in `V001__init_kaoyan_8tables.sql`)

1. `schema_migrations`: 数据库版本演进账本
2. `sys_users`: 用户账号与安全盐值哈希表
3. `user_progress_anchors`: 用户五维学习进度断点表
4. `exam_passages`: 历年考研英语真题原文与结构化段落表
5. `annotation_spans`: 精读四色标注与主谓宾成分拆解表
6. `syllabus_5500_lexicon`: 5500 考研大纲词频与熟词僻义表
7. `user_vocab_ledger`: 用户生词掌握度 $M_u$、紧急度 $S_{\text{urg}}$ 与 SM-2 调度表
8. `essay_corpus_snippets`: 大/小作文三维语料矩阵表
