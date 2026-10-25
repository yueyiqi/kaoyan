<!-- [IoC_Skill_Telemetry]
Status: VERIFIED (ev:ev-0024)
Author: antigravity (gemini-4-argon-high)
Date: 2026-10-25
Deliverable: 34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收
Evidence: ev:ev-0024
-->

# 考研英语精读平台 (`KaoyanEnglish Hub v3.6`) 借鉴 EIDS 全板块数据下钻融合方案与零 Bug 测试验收报告 (`Deliverable #34`)

> **Status**: `IMPLEMENTED` & `VERIFIED` (`ev:ev-0024` · `16/16 Live E2E PASS` · `11/11 Python Unit Tests PASS` · `8/8 Node VM UI Tests PASS` · `0 Bug`)
> **受治落盘路径**: [34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.md)
> **0-Token 前置限幅外专**: [kaoyan_admin_drilldown_shunt_engine.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_admin_drilldown_shunt_engine.py)
> **端到端真机验收脚本**: [verify_eids_drilldown_fusion_e2e.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/verify_eids_drilldown_fusion_e2e.py)
> **四模态伴生资产**: [34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.png) | [34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.svg](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.svg) | `/Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.pptx` ([34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收_slides_preview.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收_slides_preview.md)) | [34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/34_kaoyanEidsDrilldownFusion_全板块数据下钻融合验收.html)
> **生产代码锚点**: [kaoyan_eids_drilldown.js](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_eids_drilldown.js) | [kaoyan_admin_view.js](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_admin_view.js) | [kaoyan_admin_catalog.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_admin_catalog.py) | [kaoyan_http_read.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/kaoyan_http_read.py) | [index.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/index.html)

---

## 一、 前置限幅外专下钻核实：对标 `https://eids.liuzengyu.com/` 核心下钻表现与能力解构

通过对标剖析 `https://eids.liuzengyu.com/` 的前端交互源码与后端实时库表抽样架构，我们提炼出 EIDS 极具表现力的 **6 大核心下钻特性**，并一对一同化融入 `https://kaoyan-elena.duckdns.org/`：

| 序号 | `https://eids.liuzengyu.com/` 标杆下钻能力 | EIDS 原生实现机制 | `KaoyanEnglish Hub v3.6` 融合落地实现 (`kaoyan_eids_drilldown.js` + `kaoyan_admin_catalog.py`) |
| :---: | :--- | :--- | :--- |
| **1** | **双层叠跳模态弹窗系统** (`Dual-Layer Modal Overlay`) | `#detailModalOverlay` (`z-index:9998`, 展示业务实体与库表血缘映射) + `#infoModalOverlay` (`z-index:9999`, 叠层打开物理库表实时抽样与 Schema 矩阵) | 在 [`index.html`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/index.html) 挂载 `#detailModalOverlay` 与 `#infoModalOverlay` 双容器；支持从任意业务卡片先开 `L1/L2` 业务血缘详情弹窗，再一键叠跳 `L3~L5` 物理表实时抽样器，按 `ESC` 逐级平滑返回。 |
| **2** | **物理库表实时抽样浏览器** (`openLiveTableBrowser`) | `openLiveTableBrowser(tableFqn, highlightCol)` + `loadPg17TableRowsInto(...)`：弹窗顶部提供全库表切换胶囊、关键词搜索框、刷新按钮与分页器 | 实装 `openLiveTableBrowser(tableName, highlightCol, initQuery)` 与 `loadLiveTableRowsInto(...)`：支持 18 张物理表胶囊一键切换、全列关键词搜索 (`q`)、分页浏览及单行 `L4/L5` 字段显微镜下钻。 |
| **3** | **目标字段靶向高亮与自动滚动** (`highlight_col 🎯`) | 从任意业务指标或字段 Chip 点击下钻时，目标列在表头与每行单元格中以琥珀金底色 + `🎯` 徽标高亮，并自动平滑横向滚动居中 | 后端校验并返回 `highlight_col`；前端渲染表头与数据行时对匹配列施加 `.eids-col-highlight` 琥珀高亮与 `🎯` 标记，并在渲染后 `scrollIntoView({inline:'center'})`。 |
| **4** | **全库表×字段透出率与非空率矩阵** (`openOdsSchemaModal`) | EIDS `10表×115字段` 透出矩阵弹窗，展示每列非空率 (`non_null_pct`)、数据状态与点击跳表 | 后端 `build_table_exposure_matrix` 实时计算全库 **18 张表 × 146 个物理字段** 的 `non_null_rows`、`non_null_pct` 与脱敏样本值 (`sample_value`)；前端 `openOdsSchemaModal()` 渲染 18 表折叠矩阵，点击任意字段即打开该表并高亮该列。 |
| **5** | **可点击 SVG 环形图业务域下钻** (`Interactive SVG Donut`) | EIDS 顶部/总览环形图扇区绑定 `onclick`，点击扇区弹出该域下属数据源与物理表详情 | 在 `Tab 0` 架构总览新增 **五大业务与高可用域 SVG 交互环形图** (`DOM_01` ~ `DOM_05`)，点击任意扇区或右侧图例卡片即触发 `openDomainDrilldownModal(domainId)`。 |
| **6** | **跨板块业务实体血缘穿透** (`openDetailModal(lens, id)`) | 顶部 KPI 卡、产业链卡片、高校卡片、政策卡片处处可点击，弹出「业务语义 + 物理库表字段血缘映射 + 底部实时库表数据预览」 | 实装 `openDetailModal(lens, itemId)`，覆盖 `MODULE`、`BENCHMARK`、`TRACK`、`PASSAGE`、`NOTE`、`VOCAB`、`ESSAY`、`SCHEMA_TABLE` 8 类业务透镜，底部自动内嵌 `loadLiveTableRowsInto` 实时拉取对应库表行。 |

---

## 二、 全站 8 大板块 (`Top KPI` + `Tab 0 ~ Tab 6`) 下钻能力融入映射表

| 板块位置 | 板块名称 | 融入的 EIDS 下钻触发点与交互表现 | 下钻直达的物理库表与高亮字段 (`table` / `highlight_col`) |
| :--- | :--- | :--- | :--- |
| **顶部全局栏** | **Top 5 KPI 核心指标卡** | 5 张 KPI 卡片全部升级为可点击下钻卡（悬浮上浮 + 右下角 `🔍 点击下钻库表` 提示） | ① 连续打卡 ➔ `user_progress_anchors.streak_days`<br>② 精读进度 ➔ `user_progress_anchors.last_para_idx`<br>③ 批注总数 ➔ `annotation_spans.granularity`<br>④ 待复习生词 ➔ `user_vocab_ledger.urgency_score`<br>⑤ 作文模板 ➔ `essay_corpus_snippets.func_slot` |
| **`Tab 0`** | **同行对标与架构总览** | ① 新增 **18表·146列五大业务域 SVG 交互环形图** + 顶栏「18表×146列透出率矩阵」按钮 &「物理表实时浏览器」按钮；<br>② 5 大架构痛点行 (`M01~M05`) 与 6 大同行对标行 (`B01~B06`) 点击触发血缘弹窗 | `openDomainDrilldownModal('DOM_01'~'DOM_05')`、`openDetailModal('MODULE', 'M01'~'M05')`、`openDetailModal('BENCHMARK', 'B01'~'B06')` |
| **`Tab 1`** | **大纲 5500 与四轨训练** | 顶部挂载「大纲词典物理表下钻」+「个人生词账本下钻」快捷胶囊；四轨训练每一行点击弹出该训练轨道的物理表与字段血缘 | `openDetailModal('TRACK', 'Reading' \| 'Vocabulary' \| 'Writing' \| 'Translation')` ➔ `exam_passages` / `syllabus_5500_lexicon` / `essay_corpus_snippets` / `annotation_spans` |
| **`Tab 2`** | **真题双栏精读与多粒度批注** | ① 左栏真题元信息栏新增 `[🔍 真题库表血缘下钻]` 与 `[📊 物理表 exam_passages]` 按钮；<br>② 右栏每条批注卡片挂载 `[🔍 库表血缘下钻]` 按钮 | 真题卡 ➔ `openDetailModal('PASSAGE', passageId)` (`exam_passages.paragraphs_json`)；<br>批注卡 ➔ `openDetailModal('NOTE', spanId)` (`annotation_spans.selected_text`) |
| **`Tab 3`** | **5500 动态生词本** | 表头新增「查看表结构与非空率」；生词表每一行及操作栏新增 `[🔍 血缘下钻]` 按钮，弹窗内同时关联个人账本与大纲词典两张物理表 | `openDetailModal('VOCAB', lemma)` ➔ 联查 `user_vocab_ledger` (`lemma` 过滤 + 高亮 `urgency_score`) 与 `syllabus_5500_lexicon` (`polysemy_trap_note`) |
| **`Tab 4`** | **写作语料与背诵工坊** | 顶栏新增 `[🔍 语料物理表下钻]` 与 `[📊 进度锚点表]` 按钮；每张句型语料卡新增 `[🔍 库表血缘下钻]` 按钮 | `openDetailModal('ESSAY', snippetId)` ➔ `essay_corpus_snippets` (按 `snippet_id` 过滤并高亮 `cloze_pattern`) |
| **`Tab 5`** | **双擎高可用与库表架构** | ① 顶栏新增 `[📊 EIDS 18表×146列透出率矩阵]` 与 `[🔍 物理表实时抽样器]`；<br>② 库表列表每行可点击下钻，且每个字段 Chip 点击直接打开该表并靶向高亮该字段 (`🎯`) | `openDetailModal('SCHEMA_TABLE', tableName)` 或 `openLiveTableBrowser(tableName, colName)` |
| **`Tab 6`** | **管理员后台 (`2E/2F`)** | ① `2E` 五层下钻台顶栏新增 `[📊 EIDS 18表×146列透出率矩阵]` 与 `[🔍 EIDS 弹窗式实时表浏览器]`；<br>② `2F` 全库 146 字段全景字典表每行点击直接打开对应物理表并高亮该字段 | `GET /api/admin/db/drilldown` + `openLiveTableBrowser(table, column)` |

---

## 三、 全量自动化测试与公网生产集群真机验收报告 (`ev:ev-0024` · `0 Bug`)

本次升级通过 `kaoyan_admin_drilldown_shunt_engine.py`（整合 Python 后端行为单测与 Node VM 前端状态机单测）及 `verify_eids_drilldown_fusion_e2e.py`（针对公网生产集群的 16 项端到端探针）进行了全量验证，实测 **100% 通过 (`0 Bug`)**：

| 探针编号 | 验收维度与真机测试内容 | 期望结果 | 实测结果 (`ev:ev-0024`) |
| :---: | :--- | :---: | :---: |
| **`E01`** | 本地前置限幅外专与双栈行为单测 (`test_admin_drilldown.py` 11项 + `test_admin_ui.js` 8项) | `exit=0` | ✅ **PASS (`19/19 PASS`)** |
| **`E02`** | 线上首页 HTML 可达且挂载 `/kaoyan_eids_drilldown.js` | `HTTP 200` | ✅ **PASS (`len=118929`)** |
| **`E03`** | 线上首页具备 EIDS 双模态弹窗容器 (`#detailModalOverlay` + `#infoModalOverlay`) | 容器完备 | ✅ **PASS** |
| **`E04`** | 顶部 5 张 KPI 卡片全量绑定 EIDS 点击下钻事件 (`openLiveTableBrowser` + `kpi-drill-hint`) | `5/5 Cards` | ✅ **PASS (`kpi_cards=5`)** |
| **`E05`** | `Tab 0` 架构总览融入 EIDS 五大业务域 SVG 环形图与模块血缘下钻 (`MODULE` / `BENCHMARK`) | 环形图+透镜就绪 | ✅ **PASS** |
| **`E06`** | `Tab 1~5` 全板块融入 EIDS 血缘下钻 (`TRACK` / `PASSAGE` / `NOTE` / `VOCAB` / `ESSAY` / `SCHEMA`) | 6大业务透镜就绪 | ✅ **PASS** |
| **`E07`** | 线上页面零明文密码泄露且 6 处密码框具备默认掩码与 `autocomplete="new-password"` | `0 明文` | ✅ **PASS** |
| **`E08`** | 线上 `/kaoyan_eids_drilldown.js` 静态脚本可达且含四大核心下钻函数 | `HTTP 200` | ✅ **PASS (`len=32067`)** |
| **`E09`** | 未登录访客 (`GUEST`) 下钻公共表 `exam_passages` 返回 100% 字段定义与样板行 | `GUEST_TEASER` | ✅ **PASS (`18T/146C`)** |
| **`E10`** | 未登录访客 (`GUEST`) 下钻私有表 `sys_users` 仅透出 13 列结构且隐藏数据行 (`0 行泄露`) | `rows=0, cols=13` | ✅ **PASS** |
| **`E11`** | 未登录访客直接请求管理员接口 `/api/admin/db/drilldown` 刚性返回 `401` | `HTTP 401` | ✅ **PASS** |
| **`E12`** | 普通研友 (`SCHOLAR`) 登录后下钻个人生词表 `user_vocab_ledger` 返回本人记录与高亮列 | `SCHOLAR_SCOPED` | ✅ **PASS (`rows=4`)** |
| **`E13`** | 普通研友 (`SCHOLAR`) 越权请求管理员全库接口 `/api/admin/db/drilldown` 刚性返回 `403` | `HTTP 403` | ✅ **PASS** |
| **`E14`** | 管理员 (`ADMIN`) 全文检索 `q=admin` 且高亮列 `highlight_col=role` 精准命中且 13 列全透出 | `row_count=2` | ✅ **PASS** |
| **`E15`** | 管理员 (`ADMIN`) 返回 EIDS 同款 `18表×146列 table_exposure_matrix` (含非空率与脱敏样本值) | `18T / 146C` | ✅ **PASS** |
| **`E16`** | 非法 `highlight_col=nonexistent_col` 参数触发后端白名单校验返回 `400` (防注入) | `HTTP 400` | ✅ **PASS** |
