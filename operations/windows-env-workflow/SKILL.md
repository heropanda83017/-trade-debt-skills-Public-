---
name: windows-env-workflow
description: Windows 环境下 Hermes Agent 的标准操作规范。涵盖路径格式、执行工具选择、依赖安装、环境变量管理。适用于所有需要调用 execute_code / terminal / subprocess 的场景。
version: 1.0
date: 2026-05-22
tags: [windows, environment, setup, tooling]
category: operations
---

# Windows 环境工作流规范

用户明确指令：**所有操作默认走 Windows 侧，WSL/terminal 仅在必须场景使用。**

## 环境判断树

```
执行任何操作前判断：
├── 是否需要 Node.js / npx？（npm 包）
│   └── YES → 优先用 Python 替代方案（如 notion-client 而非 notion-mcp-server）
├── 是否涉及 Windows 原生工具（winget、Git、Python 包安装）？
│   └── YES → execute_code (Python subprocess)
├── 是否需要 WSL/Linux 特有工具（bash 管道、/mnt/ 中文路径）？
│   └── YES → terminal（WSL bash）
└── 混合场景
    └── 先 Windows 侧尝试，失败再降级到 terminal
```

## Windows 执行工具规范

| 场景 | 工具 | 原因 |
|------|------|------|
| Python subprocess 调用 | `execute_code`（沙盒 Python） | Windows 原生环境，网络更稳定 |
| Windows 可执行文件查找 | `shutil.which()` 先查，再用路径遍历 | 避免路径硬编码 |
| 安装 Python 包 | `subprocess.run([sys.executable, '-m', 'pip', 'install', ...])` | 避免沙盒 PATH 缺失 |
| 启动阻塞 GUI | `subprocess.Popen()` 非 `run()` | `run()` 会卡住会话 |
| 网络下载 | `urllib.request.urlretrieve()` | 无 curl/wget 时用标准库 |
| 访问 .env | `subprocess.run(..., env={**os.environ, **local_env})` | 子进程不自动继承当前 env |

## Git 安装与使用（MinGit Portable）

当系统无 Git，且 winget 不可用时，使用 MinGit Portable：

```python
# 下载
url = "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/MinGit-2.49.0-64-bit.zip"
urllib.request.urlretrieve(url, r"C:\Users\Administrator\MinGit.zip")

# 解压到固定位置
import zipfile
with zipfile.ZipFile(r"C:\Users\Administrator\MinGit.zip") as z:
    z.extractall(r"C:\Program Files\Git")

git_exe = r"C:\Program Files\Git\cmd\git.exe"
```

**gitconfig 循环包含绕过**（MinGit 系统配置损坏时）：
```python
env = os.environ.copy()
env['HOME'] = r'C:\Users\Administrator\git_home'
env['GIT_CONFIG_NOSYSTEM'] = '1'  # 禁用系统 gitconfig
subprocess.run([git_exe, 'clone', url, target], env=env)
```

## 路径格式规范

| 场景 | 格式 | 示例 |
|------|------|------|
| execute_code 中 Windows 路径 | `r'E:\...'` | `r'C:\Users\Administrator\.hermes'` |
| subprocess 中的 Python 可执行文件 | `sys.executable` | 避免硬编码 Python 路径 |
| terminal（WSL bash）路径 | `/mnt/e/...` | `/mnt/e/Landofdream/wiki/` |
| 跨平台路径（推荐） | `os.path.expanduser('~')` | 自动适配用户目录 |

## 依赖安装优先顺序

1. **pip 安装**（`subprocess.run + sys.executable`）
2. **winget**（当 pip 不可用且包在 winget 源中）
3. **MinGit Portable**（Git 类工具）
4. **urllib 直接下载**（zip/exe installer，winget 超时时）

## 创建 Hermes Skill 的目录规范（GOTCHA）

skill 目录内**任何** `.md` 文件都会被注册为独立 skill，包括子目录内的。

| 文件位置 | 后果 |
|---------|------|
| `my-skill/foo.md`（与 SKILL.md 同级） | Hermes 注册为 skill "foo"，与 "my-skill" 冲突 → `Ambiguous skill name` |
| `my-skill/references/bar.md` | 同上，references/ 里的 .md 也会被注册 |
| `my-skill/SKILL.md` + `my-skill/some-script.py` | ✅ 正确，py 文件不被当作 skill |

**正确做法：**
- Skill 目录只放 `SKILL.md` + `.py` 脚本
- 参考资料（原文、外部文档、API 引用）→ 放入项目 wiki（`E:/Landofdream/wiki/raw/`），或放在 `references/` 子目录但**不放 .md 文件**
- 辅助文件用 `.txt` / `.json` / `.py` 而非 `.md`

## Hermes Skill 双目录注册机制

Hermes 技能扫描两条路径：

| 路径 | 作用 |
|------|------|
| `~/.hermes/skills/` | 全局共享（git clone 默认装到这里） |
| `~/.hermes/profiles/<profile>/skills/` | profile 隔离（skills_list 只认这里） |

`skills_list` 读取的是 profile 下的 skills 目录。全局目录里的 skill **不会自动出现在 skills_list**。

**安装新 skill 完整流程：**
```python
import shutil, os, json
from datetime import datetime, timezone

global_src = os.path.join(hermes_dir, 'skills', 'new-skill')
profile_dst = os.path.join(profile_dir, 'skills', 'new-skill')
usage_file = os.path.join(profile_dir, 'skills', '.usage.json')

# 1. 复制到 profile skills/
shutil.copytree(global_src, profile_dst)

# 2. 注册到 .usage.json
with open(usage_file) as f:
    usage = json.load(f)

now = datetime.now(timezone.utc).isoformat()
usage['new-skill'] = {
    "archived_at": None,
    "created_at": now,
    "created_by": "agent",
    "last_patched_at": None,
    "last_used_at": None,
    "last_viewed_at": None,
    "patch_count": 0,
    "pinned": False,
    "state": "active",
    "use_count": 0,
    "view_count": 0
}

with open(usage_file, 'w') as f:
    json.dump(usage, f, indent=2)
```

**drawio-skill 特例**：SKILL.md 在 `skills/drawio-skill/SKILL.md` 嵌套子目录里，安装后需将内容提升到根目录才能被识别。

路径：`~/.hermes/profiles/<profile>/skills/.usage.json`

结构是**技能名做 key 的 flat dict**，每个技能一条记录：

```json
{
  "skill-name": {
    "created_at": "2026-05-22T14:00:00.000Z",
    "created_by": "agent",
    "last_used_at": null,
    "last_viewed_at": null,
    "use_count": 0,
    "view_count": 0,
    "state": "active",
    "pinned": false,
    "archived_at": null,
    "patch_count": 0,
    "last_patched_at": null
  }
}
```

注册新 skill 时，读取文件后直接 `usage[new_skill_name] = {...}` 写入，不要假设有 `enabled_skills` 数组。

## 多路径同步写入（skill 库文件）

当同一库文件需同步到多个目录时（常见场景：同时更新全局 `~/.hermes/skills/` 和 profile `~/.hermes/profiles/<profile>/skills/`）：

**禁止用 heredoc/三引号整体写入**，execute_code sandbox 对多行 Python 字符串有 SyntaxError。

**正确做法：**
```python
lib_code = '...\n...'  # 常规字符串拼入
target_paths = [
    pathlib.Path("C:/Users/Administrator/.hermes/skills/my-skill/lib.py"),
    pathlib.Path("C:/Users/Administrator/.hermes/profiles/land-of-dream-planning/skills/my-skill/lib.py"),
]
for p in target_paths:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(lib_code, encoding="utf-8")
    print(f"写入: {p.name}")
```

**替代方案（更安全）：** 用 `patch()` 对单段代码做精确替换，避免整体重写带来的语法风险。

## 参考资料

- `references/github-skill-evaluation.md` — GitHub skill 仓库评估流程（评估步骤/决策树/典型案例）
- `references/wechat-fetch-cf-browser-run.md` — 微信文章抓取方案（CF Browser Run REST API，无 SDK）

## ⚠️ 凭证暴露应急处理

**触发条件**：API token / secret / cookie 在对话文本中被暴露（复制粘贴、日志输出、错误信息等）。

**立即执行三步：**

1. **停止**：不继续使用当前对话 → `/new` 开新会话
2. **撤销**：到对应平台控制台**立即撤销并重新生成** token/key
3. **确认**：在 wiki/安全文档记录泄露时间、范围、已采取行动

**常见平台 revoke 地址：**
| 平台 | 地址 |
|------|------|
| Cloudflare | https://dash.cloudflare.com/profile/api-tokens |
| GitHub PAT | https://github.com/settings/tokens |
| DeepSeek | https://platform.deepseek.com/api_keys |
| Cloudflare（Account Token） | 同上，选具体 Token ID 撤销 |

**本次教训（2026-05-22）**：Cloudflare API token 在对话中暴露 → 已告知用户撤销重新生成。profile `.env` 中的 token 已存在，如需重新生成写入新值即可。

## 文件命名规范（用户指定标准）

项目所有产出文件统一命名格式：

```
YYYYMMDD_项目_内容描述_V版本.扩展名
```

### 规则

| 字段 | 说明 | 示例 |
|------|------|------|
| YYYYMMDD | 8位日期 | `20260523` |
| 项目 | 恒江雅筑 / 理想之地 / 城更公司 | `恒江雅筑` |
| 内容描述 | 中文关键词，简短 | `舆情应对实施方案` |
| V版本 | 可选，V开头 | `V2.0` |
| 扩展名 | md / docx / pdf / txt / json | `.docx` |

**分隔符统一用下划线 `_`**，不用空格、不用中文全角符号。

### 典型示例

```
20260523_恒江雅筑_舆情应对实施方案_V2.0.docx
20260523_理想之地_房票安置实施方案_V4.0.docx
20260521_恒江雅筑_学区维稳紧急报告.docx
20250916_理想之地_提请配置学区资源函_V1.0.docx
```

### 注意

- 日期统一放开头，放结尾的旧文件需逐步迁移
- 版本号用 `V` 大写，不用 `v` 或 `ver.`
- 同步更新 wiki 中对该文件的引用路径
- 源文件目录和输出目录同时遵循此规则

## Windows 文件读写工具局限性（write_file / read_file / patch）

`write_file`、`read_file`、`patch` 三个工具在 Windows E: 盘路径（如 `E:/AIGC-KB/wiki/...`）下均可能因 MSYS git-bash 内部执行 `cd C:\\Users\\Administrator` 失败而报错：

```
Failed to write file: /bin/bash: line 2: cd: C:\\Users\\Administrator: No such file or directory
```

**根因：** Hermes terminal 走 git-bash/MSYS，容器环境下 `C:\\Users\\Administrator` 目录不存在。`C:` 盘路径有同样问题，`E:` 盘路径也一样。文件工具的底层实现依赖 shell cd，而非 Windows API。

**替代方案：** 用 `execute_code` 中的 Python `open()` 直接读写文件：

```python
# 写文件（替代 write_file）
content = \"\"\"## 大标题\n内容...\"\"\"
with open(r'E:\\路径\\文件名.md', 'w', encoding='utf-8') as f:
    f.write(content)

# 读文件（替代 read_file）
with open(r'E:\\路径\\文件名.md', 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\\n')
print(f'共 {len(lines)} 行, {len(content)} 字')

# 编辑文件（替代 patch）
old = '旧文本'
new = '新文本'
if old in content:
    content = content.replace(old, new)
    with open(r'E:\\路径\\文件名.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'已替换: {content.count(new)} 处')
```

同样地，`search_files`（依赖 ripgrep）在 Windows 下也可能不可用，改用 `execute_code` + Python `os.walk()` + `glob`。

## 常见错误模式

| 错误 | 原因 | 解决 |
|------|------|------|
| `FileNotFoundError` 在 execute_code 中 | 用了 `/mnt/e/...` WSL 路径 | 改用 `E:\\...` |
| subprocess 找不到命令 | 沙盒 PATH 不含目标程序 | 用绝对路径而非命令名 |
| winget 超时 | 网络或源问题 | 改用 urllib 下载 zip |
| 环境变量不生效 | subprocess 未继承父进程 env | 显式传入 `env={**os.environ, ...}` |
| Node.js 不可用 | npx 不在 PATH | 优先用 Python 替代包（如 notion-client） |
| `Ambiguous skill name` | skill 目录内有多个 .md 文件 | 合并/删除多余的 md，只保留 SKILL.md |
| `hermes plugins list` 显示"No plugins installed"，手动复制到 `~/.hermes/plugins/` 无效 | Hermes 只扫描 `~/.hermes/profiles/<profile>/plugins/`，不扫描 `~/.hermes/plugins/` | 必须放到 `~/.hermes/profiles/<profile>/plugins/<name>/` 且 `config.yaml` 含 `plugins.enabled: [<name>]` |
| robocopy exit 16 | 长路径或权限问题，源文件被锁 | 改用 PowerShell `Move-Item`：subprocess.run(["powershell", "-Command", f"Move-Item -Path '{src}' -Destination '{dest}' -Force"]) |
| subprocess `FileNotFoundError` 但程序已安装 | winget/npm/pip 等装到自定义目录，沙盒 subprocess 找不到 | **两步走：①遍历已知路径找 exe ②注册 PATH + 直接写 JSON config 绕过命令调用**（见下方 resolve_command 代码块） |
| winget/npm 安装完但 `subprocess.run(['gh', ...])` 失败 | winget 把程序装到 `C:\Program Files\GitHub CLI` 等自定义路径，沙盒 subprocess 不继承系统 PATH | **永远不要假设 winget/npm 安装的 exe 在系统 PATH 里**，先遍历已知安装目录，找到了再注册 |

### 两步走：找到 exe → 注册 PATH + 写配置文件

当 subprocess 报 `FileNotFoundError` 但程序实际已安装时，按以下顺序处理，**两步都要做**：

```python
import shutil, os, winreg, json

def resolve_command(name, known_paths, winreg_path=None, config_file=None, config_key=None, config_entry=None):
    # Step 1: 遍历已知安装路径
    exe = shutil.which(name)
    if not exe:
        for path in known_paths:
            candidate = os.path.join(path, name if not name.endswith('.exe') else name)
            if os.path.exists(candidate):
                exe = candidate; break
    if not exe: return None

    # Step 2: 注册到系统 PATH（需管理员权限）
    if winreg_path:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0,
                winreg.KEY_READ) as key:
                current = winreg.QueryValueEx(key, 'Path')[0]
            parts = [p.strip() for p in current.split(';') if p.strip()]
            if path not in parts:
                parts.insert(0, path)
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0,
                    winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, ';'.join(parts))
        except: pass  # 非管理员则跳过 PATH 注册

    # Step 3: 写 MCP/工具 JSON config（绕过 subprocess 调用 mcporter.cmd 等场景）
    if config_file and config_entry:
        cfg = json.load(open(config_file)) if os.path.exists(config_file) else {'mcpServers': {}}
        cfg.setdefault('mcpServers', {})[config_key] = config_entry
        with open(config_file, 'w') as f: json.dump(cfg, f, indent=2)

    return exe
```

**常见程序的已知安装路径（按类型）：**

| 程序类型 | 常见路径 |
|---------|---------|
| gh (GitHub CLI) | `C:\\Program Files\\GitHub CLI\\gh.exe` | **公开数据无需 token**：`curl https://api.github.com/repos/owner/repo` 直接拿 stars/description/description。gh CLI 本身需登录才能用 `gh search`、`gh repo clone` 私有仓库 |
| mcporter.cmd | `C:\\Users\\<user>\\AppData\\Roaming\\npm\\mcporter.cmd` | 内部含 `node` 调用，node.exe 需在同目录或 PATH |
| node.exe (Node.js) | `C:\\Program Files\\nodejs\\node.exe` | npm 全局包（mcporter等）依赖此 node.exe |
| pip 全局脚本 | `C:\Program Files\Python312\Scripts\` |
| Git for Windows | `C:\Program Files\Git\cmd\` |
| Node.js | `C:\Program Files\nodejs\node.exe` |

**典型应用场景：**

```python
# gh CLI
resolve_command('gh.exe',
    known_paths=[r'C:\Program Files\GitHub CLI'],
    winreg_path=r'C:\Program Files\GitHub CLI')

# mcporter MCP server（pip install douyin-mcp-server）
resolve_command('douyin-mcp-server.exe',
    known_paths=[r'C:\Program Files\Python312\Scripts'],
    config_file=r'C:\Users\Administrator\config\mcporter.json',
    config_key='douyin',
    config_entry={"command": r'C:\Program Files\Python312\Scripts\douyin-mcp-server.exe', "args": []})

# xhs CLI（pip install xhs-cli）
resolve_command('xhs.exe',
    known_paths=[r'C:\Program Files\Python312\Scripts'])
```

## Skill 安装：git clone 完整流程（多 profile 同步）

安装一个 GitHub 上的 skill 到 Hermes，完整步骤：

### Step 0：检查并修复 gitconfig 循环包含

Git for Windows 有时会安装损坏的系统配置，导致所有 git 操作失败：

```
fatal: exceeded maximum include depth (10) while including
C:/Program Files/Git/etc/gitconfig from C:/Program Files/Git/etc/gitconfig
```

**诊断：** 读取 `C:\Program Files\Git\etc\gitconfig`，看末尾是否有 `[include]` 段落引用自身。

**修复：** Python 直接重写文件，去掉 include 段落：
```python
gitconfig_path = r'C:\Program Files\Git\etc\gitconfig'
with open(gitconfig_path, encoding='utf-8', errors='replace') as f:
    content = f.read()

# 去掉 [include] 及其后续 path 行
lines = content.split('\n')
fixed = []
skip = False
for line in lines:
    if line.strip() == '[include]':
        skip = True
        continue
    if skip:
        if line.strip() == '' or (line and not line[0].isspace()):
            skip = False  # 遇到非缩进行，结束跳过
        else:
            continue
    fixed.append(line)

with open(gitconfig_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed))
```

`git config --global` 无法绕过此问题，必须改文件。

### Step 1：找 git 可执行文件

```python
import shutil, subprocess, os

# 优先从 PATH 找
result = subprocess.run(['where', 'git'], capture_output=True, text=True)
if result.returncode == 0:
    git_cmd = result.stdout.strip().split('\n')[0]
else:
    # 常见路径遍历
    for p in [r'C:\Program Files\Git\cmd\git.exe',
              r'C:\Program Files\Git\bin\git.exe']:
        if os.path.exists(p):
            git_cmd = p
            break
```

### Step 2：克隆到全局 skills 目录

```python
target = os.path.join(os.environ['USERPROFILE'], '.hermes', 'skills', 'skill-name')
result = subprocess.run(
    [git_cmd, 'clone', '--depth=1', url, target],
    capture_output=True, text=True, timeout=90, cwd=os.path.dirname(target)
)
```

### Step 3：处理嵌套 SKILL.md（drawio-skill 等特例）

部分 skill 的 SKILL.md 不在根目录，而在 `skills/skill-name/SKILL.md` 子目录。需提升到根目录：

```python
inner = os.path.join(target, 'skills', 'skill-name')
if os.path.exists(inner):
    for item in os.listdir(inner):
        shutil.move(os.path.join(inner, item), os.path.join(target, item))
    # 清理空目录
    for d in ['skills', 'skills/skill-name']:
        p = os.path.join(target, d)
        if os.path.exists(p):
            try: os.rmdir(p)
            except: shutil.rmtree(p)
```

### Step 4：同步到所有 profile

```python
import json
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat()
profiles_dir = r'C:\Users\Administrator\.hermes\profiles'

for profile in os.listdir(profiles_dir):
    skills_dir = os.path.join(profiles_dir, profile, 'skills')
    if not os.path.isdir(skills_dir): continue

    dst = os.path.join(skills_dir, 'skill-name')
    if os.path.exists(dst): continue  # 跳过已存在的

    shutil.copytree(target, dst)  # target 是全局路径的 skill 目录

    # 注册到 .usage.json（profile 隔离）
    usage_file = os.path.join(skills_dir, '.usage.json')
    if os.path.exists(usage_file):
        with open(usage_file, encoding='utf-8') as f:
            usage = json.load(f)
    else:
        usage = {}

    usage['skill-name'] = {
        "archived_at": None, "created_at": now, "created_by": "agent",
        "last_patched_at": None, "last_used_at": None, "last_viewed_at": None,
        "patch_count": 0, "pinned": False, "state": "active",
        "use_count": 0, "view_count": 0
    }
    with open(usage_file, 'w', encoding='utf-8') as f:
        json.dump(usage, f, indent=2)
```

**当前已有 profile：** `land-of-dream-planning`、`test-migration`、`trade-debt`

**新增 skill 后必须同步到所有 profile：**

```python
import shutil, os, json
from datetime import datetime, timezone

skill_name = 'new-skill'
now = datetime.now(timezone.utc).isoformat()
src = os.path.join(os.environ['USERPROFILE'], '.hermes', 'profiles', 'land-of-dream-planning', 'skills', skill_name)

for profile in os.listdir(os.path.join(os.environ['USERPROFILE'], '.hermes', 'profiles')):
    skills_dir = os.path.join(os.environ['USERPROFILE'], '.hermes', 'profiles', profile, 'skills')
    if not os.path.isdir(skills_dir): continue
    dst = os.path.join(skills_dir, skill_name)
    if os.path.exists(dst): continue
    shutil.copytree(src, dst)
    usage_file = os.path.join(skills_dir, '.usage.json')
    usage = json.load(open(usage_file)) if os.path.exists(usage_file) else {}
    usage[skill_name] = {"archived_at": None, "created_at": now, "created_by": "agent",
        "last_patched_at": None, "last_used_at": None, "last_viewed_at": None,
        "patch_count": 0, "pinned": False, "state": "active", "use_count": 0, "view_count": 0}
    json.dump(usage, open(usage_file, 'w'), indent=2)
```

**⚠️ 此代码块因涉及 `execute_code`，下一会话需在 execute_code 中运行以完成同步。**

### Step 5：验证

调用 `skills_list()` 确认新 skill 出现在列表中。

---

## Git Clone 与 gitconfig 循环包含修复

**正确路径：先修 gitconfig，再 clone。** gitconfig 问题完全可以修复，不需要绕道 zip 下载。

### gitconfig 循环包含（根因 + 修复）

症状：
```
fatal: exceeded maximum include depth (10) while including
C:/Program Files/Git/etc/gitconfig from C:/Program Files/Git/etc/gitconfig
```

根因：Git for Windows 安装时在 `C:\Program Files\Git\etc\gitconfig` 末尾追加了 `[include]` 段落，包含自身导致循环。

修复方法（Python 直接写文件，去掉 include 段落）：
```python
gitconfig_path = r'C:\Program Files\Git\etc\gitconfig'
with open(gitconfig_path, encoding='utf-8', errors='replace') as f:
    lines = f.read().split('\n')

fixed_lines = []
skip_until_blank = False
for line in lines:
    if '[include]' in line:
        skip_until_blank = True
        continue
    if skip_until_blank:
        if line.strip() == '' or (line.strip() and not line[0].isspace()):
            skip_until_blank = False
            if line.strip() == '':
                continue
    if not skip_until_blank:
        fixed_lines.append(line)

with open(gitconfig_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))
```
修复后 git clone 立即恢复正常。`git config --global` 无效，必须直接改文件。

### 备选：GitHub ZIP 下载（当 gitconfig 修不了时）

```python
import urllib.request, zipfile, os, shutil

url = 'https://github.com/owner/repo/archive/refs/heads/main.zip'
tmp_zip = os.path.join(os.environ['TEMP'], 'repo.zip')
tmp_dir = os.path.join(os.environ['TEMP'], 'repo-tmp')

urllib.request.urlretrieve(url, tmp_zip)
with zipfile.ZipFile(tmp_zip, 'r') as z:
    z.extractall(tmp_dir)

entries = os.listdir(tmp_dir)
extracted_name = [d for d in entries if d.startswith('repo')][0]
shutil.copytree(os.path.join(tmp_dir, extracted_name, 'subdir'), target)

os.remove(tmp_zip)
shutil.rmtree(tmp_dir)
```

注意：ZIP 解压后目录名通常是 `repo-main`，`--depth=1` clone 只拿最新 commit，ZIP 没有这个优化。

## 大目录批量移动（Windows）

`robocopy /MOVE` 在长路径场景下常返回 exit 16（源路径访问失败），但 PowerShell `Move-Item` 更可靠：

```python
import subprocess, pathlib

src  = r"E:\source\BigFolder"
dest = r"E:\archive\BigFolder"

result = subprocess.run(
    ["powershell", "-Command",
     f"Move-Item -Path '{src}' -Destination '{dest}' -Force"],
    capture_output=True, text=True, timeout=300
)
# exit 0 = 成功
```

必须先用 `Test-Path` 确认源存在，Move-Item 不支持 `robocopy /MOVE /E` 那样的递归移动语义，会将整个目录树搬到目标下。
