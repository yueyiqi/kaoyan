<!-- [IoC_Skill_Telemetry]
Status: VERIFIED
Author: Antigravity (gemini-4-argon-high)
Exec: Antigravity (gemini-4-argon-high)
AutoExec: UNLOCKED
Trigger: Sandbox Persistence Escape & CamelCase Naming Escape Forensics, Treeworker Sync & GitHub Closure
Skills_Loaded: camel-case-jit-naming-and-token-shunt, slot-artifact-persistence, adaptive-presentation-compiler, completion-evidence-protocol
-->

# 沙盒路径逃逸与驼峰命名逃逸根因穿透、Treeworker 对齐及 GitHub 独立主权闭环

> [!IMPORTANT]
> **核心核实结论与根治摘要**
> 1. **当前工作区合规落盘位置与三段式驼峰目录名**：
>    - 物理路径：[`/Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台)
>    - 全量 `00` ~ `15` 共 16 套交付物（含 `.md`、`.py`、`.png`、`.svg`、`.pptx`、`_slides_preview.png`、`_slides_preview.md`、`.html`）及考研英语前后端源码已全部按 **`ADR-0701 v2.0` 三段式驼峰规范（`<序号>_<camelCase英文>_<简短中文≤12字>`）** 落盘至该目录，且内部所有 `file://` 链接 100% 指向当前工作区（**`0` 处 `~/.gemini/antigravity/brain/` 沙盒残留**）。
> 2. **为什么此前落到了 `~/.gemini/antigravity/brain/` 沙盒而没有外部工作区位置？（四环漏洞依赖链）**：
>    - **V1 (`IDE <artifacts> 提示词劫持`)** $\rightarrow$ **V2 (`编译脚本将 ART_DIR 设为 Markdown 主链接，违反 Skill 42 G10`)** $\rightarrow$ **V3 (`srbg10 稀疏检出仅含 86_，未调用 new_bz.sh 创立 95_kaoyanEnglishHub`)** $\rightarrow$ **V4 (`GATE-0522 仅在暂存 .bz/ 时触发 + pptx_preview_shunt 缺少 Rule-B3 沙盒链接拦截`)**。
> 3. **为什么 `14_*.pptx` 没有驼峰命名？是因为没有 `treeworker` 对齐吗？（三层根因穿透）**：
>    - **核实结论 (`[K]`)：是的！直接根因正是 `treeworker` 跨工作树未对齐（`cfzy0` 单槽孤岛），叠加 `ADR-0701 v1`「只管目录、漏管文件」的半截子范围漏洞！**
>    - **R1 (`treeworker 跨槽失步`)**：`ADR-0701` (`Commit 13614a8b06`) 仅在 `worker/cfzy0` 提交，既未合流 `master` (`caaac6d352`)，也未同步至 `srbg10`（`srbg10` 与 `cfzy0` 共同祖先停在 `3507a547e4 No. 5318`，相差 19 个提交），导致 `srbg10` 物理缺失 `ADR-0701` 与 `Skill 240`；
>    - **R2 (`旧闸口反向排斥驼峰`)**：未同步前，`srbg10` 上的旧版 `gate_0522` 正则为 `^[0-9]{2,3}_[a-z0-9_]+_`（不含大写 `[A-Z]`），若使用 `camelCase` 反而会被旧闸口误杀拦截；
>    - **R3 (`ADR-0701 v1 漏检文件`)**：即便在 `cfzy0` 中，原版外专与 `gate_0522` 也仅检查目录名，未检查 `.pptx` / `.md` / `.png` / `.html` 交付物文件名。
> 4. **考研英语项目提交位置主权红线（GitHub `git@github.com:yueyiqi/kaoyan.git`，严禁混入 `hp`）**：
>    - 已将 `elena` (`8.163.29.42:/home/elena/kaoyan_english_hub`) 的 PG18 双擎高可用 `v3.0` 代码及 `docs/01~15` 三段式驼峰文档全量提交并推送至 **GitHub (`git@github.com:yueyiqi/kaoyan.git`, `main` 分支)**，同时升级 `/home/elena/repos/kaoyan.git/hooks/post-receive` 实现每次 `git push prod main` 自动同步 GitHub，与母舰 `hp` 严格隔离。

![沙盒路径逃逸与驼峰命名逃逸根因穿透总览](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.png)

![沙盒逃逸与驼峰逃逸双向依赖链穿透架构图](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseFixArch_沙盒与驼峰治理架构图.png)

---

## 一、 漏洞一深度核实：为什么产出物仅落盘 `~/.gemini/antigravity/brain/` 沙盒而无工作区外部位置？

### 1.1 物理现象与危害
在上一轮交付中，`14_kaoyan_pg18_ha_12stage_architecture_diagram_PG18双擎高可用与十二阶全栈架构全景图.png` 等文件的链接指向了：
`/Users/liuzengyu/.gemini/antigravity/brain/61ebd9c2-850d-4644-86cc-9e2382f19fe7/...`
该目录属于 Antigravity IDE 内部绑定的会话级隐藏缓存目录（`~/.gemini/antigravity/brain/<conversation-id>`），不仅脱离了当前工作区 `/Users/liuzengyu/treeworker/workers/srbg10` 的业务目录树，而且一旦会话清理或跨机协作即彻底断链。

### 1.2 四环漏洞依赖链穿透 (Root-Cause Dependency Chain A)

| 依赖链环节 | 物理定位 (File & Line) | 漏洞机理穿透 (`[现象] -> [根因]`) | 根治措施 (`ADR-0701 v2.0` / `GATE-0522 v2.0`) |
| :--- | :--- | :--- | :--- |
| **Link A1: IDE `<artifacts>` 提示词劫持** | Antigravity System Prompt `<artifacts>` | 平台提示词规定 *"Only embed files that are located in `<appDataDir>/brain/<conversation-id>`"*，诱导编译脚本将 `brain` 当作默认输出靶点 | 确立 **「工作区 `.bz/` 主权真源优先 + `brain` 仅作只读镜像」** 双轨原则 |
| **Link A2: 编译脚本主指针倒置** | `01_*.py` ~ `14_*.py` (`ART_DIR` 常量) | 脚本在生成 `.md` 时直接用 `file:///.../.gemini/antigravity/brain/...` 拼接图片与交付物链接，违背 [`Skill 42 §6 G10`](file:///Users/liuzengyu/treeworker/workers/srbg10/.agents/skills/slot-artifact-persistence/SKILL.md)（严禁倒置回填 `brain`） | 重写全部 `01`~`15` 编译脚本与 `.md`，所有 `file://` 链接 100% 指向工作区 `.bz/08_.../95_kaoyanEnglishHub_考研英语精读平台/` |
| **Link A3: `srbg10` 稀疏检出未立项** | `git sparse-checkout list` (`srbg10`) | `srbg10` 默认仅检出 `.bz/08_.../86_shirong_baigong_师融百工`，未调用 [`new_bz.sh`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/5_fleet_舰仓管理/new_bz.sh) 为考研英语创立独立 `.bz/` 子项目 | 创立 [`95_kaoyanEnglishHub_考研英语精读平台`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台) 并挂载至 `srbg10` `sparse-checkout` |
| **Link A4: 门禁触发旁路与漏检** | [`gate_0522`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/gates/gate_0522_bz_naming_and_raw_material_md_guard.sh) & [`pptx_preview_shunt_engine.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/7_renderers_渲染中枢/pptx_preview_shunt_engine.py) | 原 `gate_0522` 当无 `.bz/` 文件暂存时直接 `exit 0`；原 `pptx_preview_shunt_engine.py` 仅查 `Rule-B1/B2`，未查 `brain/` 沙盒链接 | `gate_0522` 第 0 节 + `pptx_preview_shunt_engine.py` 新增 **`Rule-B3:BANNED_SANDBOX_BRAIN_PRIMARY_LINK`** 硬拦截 |

---

## 二、 漏洞二深度核实：为什么 `14_*.pptx` 没有驼峰命名？是未对齐 `treeworker` 造成的吗？

### 2.1 物理取证结论：完全属实！由 `treeworker` 跨槽未对齐 + `ADR-0701 v1` 漏管文件共同导致

通过 Git 拓扑探针与 AST 静态比对，定位出三层精确根因：

1. **第一层根因（`treeworker` 跨槽位失步 —— `cfzy0` 单槽孤岛 `[K]`）**：
   - 执行 `git branch -a --contains 13614a8b06` 实测证明：实装三段式驼峰命名法的 `No. 5414 [cfzy0] feat(governance): 实装三段式驼峰命名法与存量资产JIT双轨演进四位一体体系 (ADR-0701)` **仅存在于 `worker/cfzy0` 工作树**！
   - `master` 主干停留在 `caaac6d352 (No. 5396)`，而当前工作树 `srbg10` 与 `cfzy0` 的共同祖先 (`git merge-base HEAD worker/cfzy0`) 停留在 `3507a547e4 (No. 5318)`，相差 **19 个提交**。
   - 因此，在未对齐前，`srbg10` 工作区中物理不存在 [`ADR-0701`](file:///Users/liuzengyu/treeworker/workers/srbg10/.adr/701-800/701-710/adr_0701_camelCaseJitNamingGovernance_三段式驼峰命名与存量JIT演进/adr_0701_camelCaseJitNamingGovernance_三段式驼峰命名与存量JIT演进.md)、不存在 [`Skill 240`](file:///Users/liuzengyu/treeworker/workers/srbg10/.agents/skills/camel-case-jit-naming-and-token-shunt/SKILL.md)，也不存在 [`camel_case_jit_naming_shunt_engine.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/camel_case_jit_naming_shunt_engine.py)。
2. **第二层根因（`srbg10` 旧版 `gate_0522` 正则反向排斥大写驼峰 `[K]`）**：
   - 未对齐前，`srbg10` 上的 `gate_0522` 仍使用旧版正则 `r'^[0-9]{2,3}_[a-z0-9_]+_'`（仅允许小写字母与下划线）。如果当时直接使用 `camelCase` 大写字母，反而会被旧版 `gate_0522` 当作非法命名拦截！
3. **第三层根因（`ADR-0701 v1` 自身“只管目录、不管文件”的范围盲区 `[K]`）**：
   - 审查 `cfzy0` 的 `13614a8b06` 发现，原版 `camel_case_jit_naming_shunt_engine.py` 与 `gate_0522` **仅检查子项目目录名 (`os.path.isdir`)**，完全没有检查目录内部的交付物文件名（如 `14_*.pptx`、`14_*.md`、`14_*.png`、`14_*.html`），也没有处理 `.pptx` 扩展名与 `_slides_preview.png` 伴生后缀。
   - 现已将 [`camel_case_jit_naming_shunt_engine.py`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/camel_case_jit_naming_shunt_engine.py) 与 [`gate_0522`](file:///Users/liuzengyu/treeworker/workers/srbg10/scripts/3_governance_治理门禁/gates/gate_0522_bz_naming_and_raw_material_md_guard.sh) 升级至 **v2.0** 并跨槽同步至 `srbg10`、`cfzy0`、`srbg0`：新增 `--mode audit-files` 与 `gate_0522` 第 3.5 节，强制所有新增序号化交付文件主干满足 `^[0-9]{2,3}_[a-z][a-zA-Z0-9]*_[一-龥A-Za-z0-9\-]{2,12}$`！

---

## 三、 当前工作区 `95_kaoyanEnglishHub_考研英语精读平台` 全量产出物三段式驼峰落盘对照表

所有产出物均已按 `<序号>_<camelCase英文>_<简短中文≤12字>.<ext>` 落盘至当前工作区目录 [`/Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/`](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台)：

| 原 `snake_case` 冗长文件名 | 新 `ADR-0701 v2.0` 三段式驼峰文件名 | 字符数变化 | BPE Token 变化 (`o200k_base`) |
| :--- | :--- | :--- | :--- |
| `01_kaoyan_english_web_semantic_spec_and_prd_考研英语真题精读词汇作文一体化网站语义单与PRD大典.html` | `01_kaoyanWebSrsPrd_考研网站语义单与PRD.html` | `75 -> 35` (`-40`) | `38 -> 21` (`-17`) |
| `01_kaoyan_english_web_semantic_spec_and_prd_考研英语真题精读词汇作文一体化网站语义单与PRD大典.md` | `01_kaoyanWebSrsPrd_考研网站语义单与PRD.md` | `73 -> 33` (`-40`) | `38 -> 21` (`-17`) |
| `01_kaoyan_english_web_semantic_spec_and_prd_考研英语真题精读词汇作文一体化网站语义单与PRD大典.png` | `01_kaoyanWebSrsPrd_考研网站语义单与PRD.png` | `74 -> 34` (`-40`) | `38 -> 21` (`-17`) |
| `01_kaoyan_english_web_semantic_spec_and_prd_考研英语真题精读词汇作文一体化网站语义单与PRD大典.pptx` | `01_kaoyanWebSrsPrd_考研网站语义单与PRD.pptx` | `75 -> 35` (`-40`) | `40 -> 23` (`-17`) |
| `02_kaoyan_english_web_v2_peer_benchmark_and_frontend_ux_optimization_spec_考研英语网站主流竞品对标与前端学习效果优化方案v2大典.md` | `02_kaoyanPeerBenchmarkUxV2_竞品对标与前端优化.md` | `104 -> 39` (`-65`) | `44 -> 20` (`-24`) |
| `03_kaoyan_web_ssl_err_root_cause_and_v2_live_remediation_spec_考研英语网站SSL断连根因穿透与v2真机修复实装大典.md` | `03_kaoyanSslFixLiveV2_SSL根因与真机修复.md` | `91 -> 35` (`-56`) | `42 -> 19` (`-23`) |
| `04_elena_nonroot_tiered_storage_and_t2_cold_backup_spec_主机elena普通账号部署与冷热数据分层及T2归档大典.md` | `04_elenaNonrootTieredStorage_非Root分层与T2冷备.md` | `86 -> 44` (`-42`) | `37 -> 19` (`-18`) |
| `05_elenalyl_top_unreachable_root_cause_and_hk_edge_proxy_spec_elenalyl域名ERR_CONNECTION_CLOSED根因与香港边缘回源方案.md` | `05_elenalylEdgeProxySpec_域名阻断根因与回源.md` | `107 -> 37` (`-70`) | `37 -> 19` (`-18`) |
| `07_blade_router_tiering_and_elenalyl_status_probe_刀刃路由档位修复与域名上线阻塞现状.md` | `07_bladeRouterTieringProbe_刀刃路由与域名探针.md` | `70 -> 39` (`-31`) | `32 -> 19` (`-13`) |
| `09_kaoyan_elenalyl_top_deployment_and_ssl_test_report_kaoyan域名部署与证书访问全链路测试报告.md` | `09_kaoyanSslDeployReport_域名部署与证书测试.md` | `79 -> 37` (`-42`) | `33 -> 17` (`-16`) |
| `10_windows_ssh_passwordless_config_and_elena_pubkey_spec_Windows免密登录8.163.29.42完整配置与公钥部署方案.md` | `10_windowsSshPubkeyConfig_Win免密配置与部署.md` | `93 -> 39` (`-54`) | `33 -> 15` (`-18`) |
| `11_student_ssh_git_contradiction_forensics_and_vscode_deploy_loop_spec_截图与免密登录矛盾穿透取证及VSCode一键发布闭环方案.md` | `11_sshGitContradictionFix_免密矛盾取证与发布.md` | `102 -> 38` (`-64`) | `40 -> 19` (`-21`) |
| `12_ssh_passwordless_login_framework_uml_swimlane_and_5_visual_paradigms_spec_SSH免密登录与Git发布框架UML泳道图及五大可视化全景大典.html` | `12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.html` | `113 -> 45` (`-68`) | `47 -> 21` (`-26`) |
| `12_ssh_passwordless_login_framework_uml_swimlane_and_5_visual_paradigms_spec_SSH免密登录与Git发布框架UML泳道图及五大可视化全景大典.md` | `12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.md` | `111 -> 43` (`-68`) | `47 -> 21` (`-26`) |
| `12_ssh_passwordless_login_framework_uml_swimlane_and_5_visual_paradigms_spec_SSH免密登录与Git发布框架UML泳道图及五大可视化全景大典.png` | `12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.png` | `112 -> 44` (`-68`) | `47 -> 21` (`-26`) |
| `12_ssh_passwordless_login_framework_uml_swimlane_and_5_visual_paradigms_spec_SSH免密登录与Git发布框架UML泳道图及五大可视化全景大典.pptx` | `12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.pptx` | `113 -> 45` (`-68`) | `49 -> 23` (`-26`) |
| `13_windows_kaoyan_https_publishing_architecture_diagram_Windows发布HTTPS全链路架构图.png` | `13_windowsHttpsPublishArch_Win发布架构图.png` | `80 -> 39` (`-41`) | `24 -> 12` (`-12`) |
| `13_windows_kaoyan_https_site_publishing_master_summary_spec_Windows视角考研英语HTTPS站点发布全链路总结大典.html` | `13_windowsKaoyanHttpsSummary_Win视角发布总结.html` | `94 -> 43` (`-51`) | `31 -> 14` (`-17`) |
| `13_windows_kaoyan_https_site_publishing_master_summary_spec_Windows视角考研英语HTTPS站点发布全链路总结大典.md` | `13_windowsKaoyanHttpsSummary_Win视角发布总结.md` | `92 -> 41` (`-51`) | `31 -> 14` (`-17`) |
| `13_windows_kaoyan_https_site_publishing_master_summary_spec_Windows视角考研英语HTTPS站点发布全链路总结大典.png` | `13_windowsKaoyanHttpsSummary_Win视角发布总结.png` | `93 -> 42` (`-51`) | `31 -> 14` (`-17`) |
| `13_windows_kaoyan_https_site_publishing_master_summary_spec_Windows视角考研英语HTTPS站点发布全链路总结大典.pptx` | `13_windowsKaoyanHttpsSummary_Win视角发布总结.pptx` | `94 -> 43` (`-51`) | `33 -> 16` (`-17`) |
| `14_kaoyan_pg18_ha_12stage_architecture_diagram_PG18双擎高可用与十二阶全栈架构全景图.png` | `14_kaoyanPg18HaArchDiagram_PG18高可用架构图.png` | `71 -> 41` (`-30`) | `37 -> 20` (`-17`) |
| `14_kaoyan_pg18_ha_fullstack_12stage_architecture_and_acceptance_spec_考研英语全栈PG高可用架构十二阶设计与测试验收大典.html` | `14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.html` | `99 -> 46` (`-53`) | `43 -> 22` (`-21`) |
| `14_kaoyan_pg18_ha_fullstack_12stage_architecture_and_acceptance_spec_考研英语全栈PG高可用架构十二阶设计与测试验收大典.md` | `14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.md` | `97 -> 44` (`-53`) | `43 -> 22` (`-21`) |
| `14_kaoyan_pg18_ha_fullstack_12stage_architecture_and_acceptance_spec_考研英语全栈PG高可用架构十二阶设计与测试验收大典.png` | `14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.png` | `98 -> 45` (`-53`) | `43 -> 22` (`-21`) |
| `14_kaoyan_pg18_ha_fullstack_12stage_architecture_and_acceptance_spec_考研英语全栈PG高可用架构十二阶设计与测试验收大典.pptx` | `14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.pptx` | `99 -> 46` (`-53`) | `45 -> 24` (`-21`) |
| `(新增 #15 主文档/PPTX/HTML)` | `15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.{md,png,pptx,html}` | `49 chars` | `20 tokens (100% NEW_CAMEL_COMPLIANT)` |

---

## 四、 考研英语项目 GitHub (`git@github.com:yueyiqi/kaoyan.git`) 独立提交与同步闭环

遵循统帅明确指令（**“考研英语项目提交的位置要在 GitHub 的，不是 hp 或其它位置”**）：
1. **GitHub 唯一远端绑定**：线上生产工作树 `elena` (`8.163.29.42:/home/elena/kaoyan_english_hub`) 的 `origin` 严格绑定为 `git@github.com:yueyiqi/kaoyan.git`（严禁指向 `git@hp:`）。
2. **全量代码与 `docs/01~15` 三段式驼峰文档入库推送**：
   - 已清理 `/home/elena/kaoyan_english_hub/docs/` 下的旧版下划线文档，将 `01_kaoyanWebSrsPrd_考研网站语义单与PRD.md` ~ `15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.md` 等全套驼峰工程文档与 PG18 双擎高可用 `v3.0` 代码一并提交至 `main` 分支，并直接推送至 **GitHub `origin/main` (`git@github.com:yueyiqi/kaoyan.git`)**。
3. **`post-receive` 钩子自动双推加固**：
   - 已升级 `/home/elena/repos/kaoyan.git/hooks/post-receive`：当 Windows 端执行 `git push prod main` 时，不仅自动检出更新 `/home/elena/kaoyan_english_hub` 并重启 `kaoyan-english-hub.service`，同时自动执行 `git -C /home/elena/kaoyan_english_hub push origin main` 实时同步至 GitHub！

---

## 五、 当前工作区全量核心交付物直达链接 (`95_kaoyanEnglishHub_考研英语精读平台`)

### 5.1 本次根因穿透与驼峰治理四件套 (`15_*`)
1. **根因穿透与治理规范 (`.md`)**：[15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.md)
2. **2x2 Bento 根因与治理总览图 (`.png`)**：[15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.png)
3. **双向依赖链与 GitHub 闭环架构图 (`.png`)**：[15_sandboxCamelCaseFixArch_沙盒与驼峰治理架构图.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseFixArch_沙盒与驼峰治理架构图.png)
4. **原生 MSU 演示文稿 (`.pptx` · 5 页)**：`/Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.pptx`（高清预览网格：[15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理_slides_preview.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理_slides_preview.png) | 逐页画册：[15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理_slides_preview.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理_slides_preview.md)）
5. **交互式三模态审查工作台 (`.html`)**：[15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/15_sandboxCamelCaseEscapeFix_沙盒与驼峰逃逸根因治理.html)

### 5.2 已重命名并迁移至当前工作区的核心全模态交付物 (`01_*`, `12_*`, `13_*`, `14_*`)
- **#14 PG18 双擎高可用十二阶设计与 24 项真机验收**：
  - 文档：[14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.md)
  - 总览图：[14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.png) | 架构图：[14_kaoyanPg18HaArchDiagram_PG18高可用架构图.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaArchDiagram_PG18高可用架构图.png)
  - 演示文稿：`/Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.pptx`（预览网格：[14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收_slides_preview.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收_slides_preview.png)）
  - 交互工作台：[14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.html](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/14_kaoyanPg18HaFullstackSpec_PG18高可用十二阶验收.html)
- **#13 Windows 视角 HTTPS 站点发布总结**：
  - 文档：[13_windowsKaoyanHttpsSummary_Win视角发布总结.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/13_windowsKaoyanHttpsSummary_Win视角发布总结.md) | 架构图：[13_windowsHttpsPublishArch_Win发布架构图.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/13_windowsHttpsPublishArch_Win发布架构图.png) | 预览网格：[13_windowsKaoyanHttpsSummary_Win视角发布总结_slides_preview.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/13_windowsKaoyanHttpsSummary_Win视角发布总结_slides_preview.png)
- **#12 SSH 免密登录与 Git 发布 UML 泳道图**：
  - 文档：[12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/12_sshPasswordlessUmlSwimlane_免密框架UML泳道图.md) | Win 泳道图：[12_windowsSshSwimlaneDiag_Win视角免密UML泳道图.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/12_windowsSshSwimlaneDiag_Win视角免密UML泳道图.png) | 预览网格：[12_sshPasswordlessUmlSwimlane_免密框架UML泳道图_slides_preview.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/12_sshPasswordlessUmlSwimlane_免密框架UML泳道图_slides_preview.png)
- **#01 考研英语网站语义单与 PRD**：
  - 文档：[01_kaoyanWebSrsPrd_考研网站语义单与PRD.md](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/01_kaoyanWebSrsPrd_考研网站语义单与PRD.md) | 总览图：[01_kaoyanWebSrsPrd_考研网站语义单与PRD.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/01_kaoyanWebSrsPrd_考研网站语义单与PRD.png) | 预览网格：[01_kaoyanWebSrsPrd_考研网站语义单与PRD_slides_preview.png](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/01_kaoyanWebSrsPrd_考研网站语义单与PRD_slides_preview.png)
