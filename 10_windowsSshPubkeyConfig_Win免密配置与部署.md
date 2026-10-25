# Windows 主机免密访问 `8.163.29.42` (`elena`) 公钥部署核验与客户端一键配置大典

```yaml
[IoC_Skill_Telemetry]
Node_ID: srbg10
Agent: antigravity
LLM_Model: gemini-4-argon-high
Task_EB: eb_9036_srbg10_H_antigravity_gemini-4-argon-high_kaoyan-english-web-semantic-spec-and-prd-shunt
Status: VERIFIED
Evidence_IDs:
  - ev:ev-0025
  - ev:ev-0026
Skills_Mounted:
  - completion-evidence-protocol (Skill 195)
```

---

## 一、 远端 `8.163.29.42` 公钥部署实测状态 (`VERIFIED` `ev:ev-0025`, `ev:ev-0026`)

| 核验维度 | `elena` 普通管理账号（推荐首选，带免密 `sudo`） | `root` 超管账号 |
| :--- | :--- | :--- |
| **`authorized_keys` 路径** | `/home/elena/.ssh/authorized_keys` | `/root/.ssh/authorized_keys` |
| **已落盘完整公钥** | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFESj+nOVBhNImRjKod9BM+72uvv3Xf57mD+o9Ywnkkr cl-715-codeup` | 同左 |
| **`ssh-keygen -lf` 指纹** | `256 SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw cl-715-codeup (ED25519)` | 同左 |
| **目录与文件权限** | `/home/elena/.ssh` (`700 elena:elena`)<br>`authorized_keys` (`600 elena:elena`) | `/root/.ssh` (`700 root:root`)<br>`authorized_keys` (`600 root:root`) |
| **服务端 `sshd` 策略** | `PubkeyAuthentication yes` / `PasswordAuthentication no` | `PermitRootLogin prohibit-password` |

伴生自动核验脚本：[10_windowsSshPubkeyConfig_Win免密配置与部署.py](file:///Users/liuzengyu/treeworker/workers/srbg10/.bz/08_research_frontier_前沿研究与探索验证/95_kaoyanEnglishHub_考研英语精读平台/10_windowsSshPubkeyConfig_Win免密配置与部署.py)

---

## 二、 Windows 客户端免密登录完整配置方案 (PowerShell / CMD / VS Code / Cursor / Antigravity)

### 2.1 第一步：确认 Windows 私钥路径与权限收敛（防 OpenSSH `UNPROTECTED PRIVATE KEY FILE` 报错）

在 Windows 上打开 **PowerShell**，执行以下命令检查私钥并自动修复 Windows NTFS 权限（Windows OpenSSH 要求私钥文件只能由当前用户读取，否则会拒绝使用私钥并退回询问密码）：

```powershell
# 1. 查看 ~/.ssh 目录下的私钥文件（通常为 id_ed25519）
Get-ChildItem "$env:USERPROFILE\.ssh"

# 2. 校验本地公钥指纹是否与服务端 SHA256:OFeU8L1Blc+ECOmWayawRMLIYace0UuxIVM+ojmTNiw 一致
ssh-keygen -lf "$env:USERPROFILE\.ssh\id_ed25519.pub"

# 3. 修复 Windows 下私钥文件权限（消除 Permissions are too open 报错）
$KeyPath = "$env:USERPROFILE\.ssh\id_ed25519"
icacls $KeyPath /inheritance:r
icacls $KeyPath /grant:r "$($env:USERNAME):(R)"
```

> **提示**：如果您的私钥文件名不是 `id_ed25519`（例如叫 `id_ed25519_codeup`），请将上面和下方配置中的 `id_ed25519` 替换为实际私钥文件名。

---

### 2.2 第二步：一键写入 Windows `~/.ssh/config` 主机别名配置

在 Windows **PowerShell** 中直接粘贴运行以下整段脚本，即可自动在 `C:\Users\<用户名>\.ssh\config` 中写入 `elena` 和 `elena-root` 两个免密别名：

```powershell
$SshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $SshDir)) { New-Item -ItemType Directory -Path $SshDir | Out-Null }

$ConfigBlock = @"

# === Elena ECS (8.163.29.42) Passwordless Access ===
Host elena
    HostName 8.163.29.42
    User elena
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3

Host elena-root
    HostName 8.163.29.42
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
"@

Add-Content -Path "$SshDir\config" -Value $ConfigBlock -Encoding UTF8
Write-Host "[OK] ~/.ssh/config 已写入 elena 与 elena-root 免密配置！" -ForegroundColor Green
```

---

### 2.3 第三步：在 Windows 终端 / VS Code / SCP 中免密直连验证

配置完成后，在 Windows 任意终端（PowerShell / Windows Terminal / Git Bash）或 IDE（VS Code / Cursor / Antigravity `Remote-SSH`）中直接输入：

```powershell
# 1. 日常运维与业务部署（推荐：直接进 elena 账号，自带免密 sudo）
ssh elena

# 2. 如需直接以 root 身份进入
ssh elena-root

# 3. 免密上传/下载文件示例 (SCP)
scp .\local_file.txt elena:/home/elena/kaoyan_english_hub/
```

---

### 2.4 第四步（可选）：若私钥设了 Passphrase 口令，启用 Windows `ssh-agent` 开机免输口令

如果您生成 `cl-715-codeup` 密钥对时设置了私钥保护密码（Passphrase），可在管理员 PowerShell 中开启 Windows 原生 `ssh-agent` 服务，实现托管免输：

```powershell
# 以管理员身份打开 PowerShell 执行一次：
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent

# 将私钥加入 Windows ssh-agent 内存托管：
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
```
