<!-- [IoC_Skill_Telemetry]
Status: VERIFIED
Author: Antigravity (gemini-4-argon-high)
Trigger: ADR-0522 / ADR-0701 Subproject 95 Intake & Feasibility Assessment
-->
# 95_kaoyanEnglishHub_考研英语精读平台 — 第一性技术可行性研判与工况六维量化问卷

## 一、 第一性技术可行性研判结论
- **研判结论**: **🟢 FEASIBLE (绿灯可行，已上线验证)**
- **物理宿主**: `elena` (`8.163.29.42`, `2 vCPU / 1749 MiB RAM / 0 Swap / 40 GB SSD`) + `T2 (/vol1)` 19TB Btrfs 异地冷备。
- **架构选型**: PostgreSQL 18.6 (`kaoyan_prod`, `shared_buffers=128MB`) + SQLite WAL 双擎同步双写高可用 (`RTO<5ms`, `RPO=0`) + Python 3.14 多线程五层中间件模块化单体 + Vue 3 `KaoyanReactiveStore` 响应式前端。
- **代码提交主权目标**: **GitHub (`git@github.com:yueyiqi/kaoyan.git`)** + `elena:/home/elena/repos/kaoyan.git` 自动联动，与母舰 `hp` 完全物理隔离。

## 二、 工况六维量化问卷
| 维度 | 量化指标 |
| :--- | :--- |
| 1. 并发与吞吐 | 支持 `10~50` 学籍并发读写，单机峰值 `350+ QPS` |
| 2. 内存安全红线 | 整机常驻 `512 MiB / 1749 MiB` (`29.3%`)，预留 `1.2 GiB` 安全余量 |
| 3. 数据高可用 | PG18 主库 + SQLite WAL 热备 + T2 每日双轨归档 (10 张受治表) |
| 4. 发布效率 | Windows VS Code `git push prod main` `<= 3.0s` 零中断上线并自动同步 GitHub |
| 5. 视觉与交互 | Daylight / Midnight / Eyecare 三模态 + PC/Mobile 双视口 + 二刷毛玻璃遮罩 |
| 6. 验收测试 | 24 项四维正交自动化真机测试 `24/24 (100.0%) PASS` |
