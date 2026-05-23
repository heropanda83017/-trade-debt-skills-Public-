# res-downloader Windows 部署指南（WSL → Windows 工作流）

> 最后更新：2026-05-05 | 部署来源：putyy/res-downloader v3.1.3
> 适用场景：从 WSL 终端下载 GitHub Releases 软件并部署到 Windows 环境

## 前置条件

- WSL2 环境，D 盘已挂载到 `/mnt/d/`
- 已知 Windows 用户名（本例：`heropanda`）
- GitHub Releases API 可访问
- Windows PowerShell 可用（路径：`/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`）

## 完整部署流程

### 第一步：创建目录

```bash
mkdir -p /mnt/d/res-downloader
```

### 第二步：从 GitHub Releases 下载

下载地址从 GitHub Release API 获取，选择对应的 Windows 版本：

```bash
cd /mnt/d/res-downloader
curl -L -o res-downloader_3.1.3_win_amd64.exe \
  "https://github.com/putyy/res-downloader/releases/download/3.1.3/res-downloader_3.1.3_win_amd64.exe" \
  --progress-bar
```

**版本选择依据：**
| 文件 | 适用架构 | 典型下载量 |
|------|---------|-----------|
| `*_win_amd64.exe` | 主流 Intel/AMD x64 | ~38,000+ |
| `*_win_arm64.exe` | Surface Pro X 等 ARM | ~8,500+ |

### 第三步：SHA256 完整性校验

**方法一：对照 GitHub Release API 元数据（推荐）**

```bash
# 本地计算哈希
sha256sum res-downloader_3.1.3_win_amd64.exe
# 输出示例: ac0ede0e25b5ff687ad56098bf9757e428ca0d6126c677546ed77652ef967344

# 通过 API 获取官方哈希
curl -sL "https://api.github.com/repos/putyy/res-downloader/releases/latest" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'{a[\"name\"]}: {a[\"digest\"]}') for a in d['assets']]"
```

校验要点：
- GitHub API 返回的 `digest` 字段格式为 `sha256:xxxxxxxx...`
- 本地 `sha256sum` 输出为纯哈希值
- 对比时去掉 API 返回的 `sha256:` 前缀，核对后续 64 位十六进制字符串

**方法二：直接对比本文记录的已知哈希**

| 版本 | 文件 | SHA256 |
|------|------|--------|
| v3.1.3 | win_amd64.exe | `ac0ede0e25b5ff687ad56098bf9757e428ca0d6126c677546ed77652ef967344` |
| v3.1.3 | win_arm64.exe | `c30e202d1991562c13ba5f860b011a8838923395381d5e949e3a7f4d6e41f52a` |

> ⚠️ 每次下载新版本前，务必从 GitHub API 获取最新哈希，不要直接相信上述记录

### 第四步：创建桌面快捷方式（通过 PowerShell）

**重要：从 WSL 调用 PowerShell 的两种方法对比**

| 方法 | 优点 | 缺点 |
|------|------|------|
| `-File` 执行 .ps1 脚本 | 脚本可复用 | ⚠️ 编码问题：WSL 写入的 UTF-8 无 BOM 文件，PowerShell 解析中文报错 |
| `-Command` 直接传脚本（推荐） | **无编码问题**，一行搞定 | 适合较短脚本 |

**推荐方法：用 `-Command` 直接传 PowerShell 命令（避免文件编码问题）**

```python
# 在 Hermes execute_code 中执行
import subprocess
ps = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'

# 使用 PowerShell 单引号字符串（纯 ASCII，无编码问题）
script = """
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\res-downloader.lnk')
$s.TargetPath = 'D:\\res-downloader\\res-downloader_3.1.3_win_amd64.exe'
$s.WorkingDirectory = 'D:\\res-downloader'
$s.Save()
Write-Host 'ok'
"""

result = subprocess.run(
    [ps, '-ExecutionPolicy', 'Bypass', '-Command', script],
    capture_output=True, timeout=30
)
# 注意：Windows 控制台输出编码为 GBK，需用 gbk 解码
stdout = result.stdout.decode('gbk', errors='replace').strip()
print('Result:', stdout)
```

**备用方法（脚本文件方式）：**

```python
# 1. 用 write_file 工具写入纯 ASCII 版 .ps1（避免中文字符）
ps1_content = '''$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + "\\res-downloader.lnk")
$s.TargetPath = "D:\\res-downloader\\res-downloader_3.1.3_win_amd64.exe"
$s.WorkingDirectory = "D:\\res-downloader"
$s.Description = "res-downloader v3.1.3"
$s.Save()
if (Test-Path ([Environment]::GetFolderPath('Desktop') + "\\res-downloader.lnk")) \\\
  { Write-Host "OK" } else { Write-Host "FAIL"; exit 1 }
'''
write_file('/mnt/d/res-downloader/create-shortcut.ps1', ps1_content)

# 2. 通过 WSL 执行 PowerShell -File
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -ExecutionPolicy Bypass \
  -File D:\\res-downloader\\create-shortcut.ps1
```

**快捷方式验证：**

```bash
# 通过 PowerShell 列出桌面所有 .lnk
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -ExecutionPolicy Bypass \
  -Command "Get-ChildItem ([Environment]::GetFolderPath('Desktop')) -Filter '*.lnk' | Select-Object Name"
```

> **为什么 WSL 的 `ls` 看不到 .lnk 文件？**
> Windows 桌面可能包含系统保护文件，WSL 的 Linux 文件系统驱动不会列出所有 Windows 桌面项。始终使用 PowerShell `Get-ChildItem` 来验证。

### 第五步：验证部署完整性

```bash
ls -lh /mnt/d/res-downloader/
# 预期文件结构：
# D:\res-downloader\
#   ├── res-downloader_3.1.3_win_amd64.exe   (11MB, 主程序)
#   ├── create-shortcut.ps1                   (备用，可重新生成快捷方式)
#   └── (后续可添加: 配置文件、下载缓存等)
```

## 故障排查

### 1. PowerShell 脚本执行报错 "UnexpectedToken"

**原因：** WSL 写入的 .ps1 文件编码为 UTF-8 without BOM，PowerShell 对中文字符解析异常。

**解决：** 脚本中完全避免中文字符，或用 Python 的 `write_file` 工具写入纯 ASCII 版本。

### 2. 快捷方式已创建但桌面图标不显示

**原因：** 桌面刷新问题，或 lnk 文件目标路径不存在。

**解决：** 桌面右键 → 刷新，或直接双击 .lnk 确认路径是否正确。

### 3. 权限不足

**原因：** 公司 IT 管控，PowerShell 执行策略限制。

**解决：** 改用管理员身份运行 PowerShell，或手动复制快捷方式。

### 4. 代理冲突

如果公司网络已配置系统代理，res-downloader 的 8899 代理可能与之冲突。在软件设置中修改代理端口即可。

## 相关文件

- `video-downloading.md` — res-downloader 的**使用指南**（本文件覆盖的是**部署安装**）
- GitHub 原仓库: https://github.com/putyy/res-downloader
