---
name: agent-reach
description: 互联网多平台数据采集工具箱。通过 yt-dlp、GitHub API、xhs-cli、mcporter MCP servers 等采集 YouTube/GitHub/小红书/抖音/微博等平台数据。触发词：「抓取YouTube」「搜小红书」「GitHub trending」「查抖音」「查微博舆情」。
version: 1.0
date: 2026-05-22
tags: [web-scraping, social-media, youtube, github, xiaohongshu, douyin]
category: operations
---

## 当前可用渠道（2026-05-22，v2）

| 平台 | 工具 | 状态 | 数据类型 | cookie需求 |
|------|------|------|---------|-----------|
| YouTube | yt-dlp | ✅ 即用 | 标题/播放量/字幕/评论/元数据 | 无 |
| GitHub | curl REST API | ✅ 即用 | trending/仓库stars/代码搜索 | 无（公开数据） |
| Weibo | mcporter weibo MCP | ✅ 即用 | 热搜/博文/评论搜索 | 无 |
| Exa | mcporter exa MCP | ✅ 即用 | 语义搜索（可搜微信文章） | 无 |
| RSS | agent-reach 内置 | ✅ 即用 | HackerNews/V2EX等 | 无 |
| 抖音 | mcporter douyin-mcp | ✅ 3/3 healthy | 视频信息/搜索（5工具） | 需 cookie 增强 |
| 小红书 | xhs-cli + Edge CDP | ✅ 可用 | 笔记搜索/详情 | 需 cookie |
| Reddit | rdt-cli | ⏳ 需登录 | 热帖/评论 | 需 cookie |
| Bilibili | yt-dlp 内置 | ✅ 即用 | 视频元数据/字幕 | 无 |
| Xueqiu | agent-reach 内置 | ✅ 可用 | 雪球财经帖子 | 无 |

## 核心工具

### yt-dlp — YouTube/Bilibili/抖音

```python
# YouTube 视频元数据（无需 cookie）
subprocess.run(['yt-dlp', '--dump-json', '--no-playlist',
    'https://www.youtube.com/watch?v=VIDEO_ID'],
    capture_output=True, text=True, timeout=20)
# 返回: title, uploader, view_count, duration, tags, upload_date

# 抖音视频（需登录 cookie，否则报错）
# yt-dlp 支持 youtube/bilibili/douyin/xiaohongshu/weibo 等 1000+ extractor
```

## GitHub 自动化（PAT token）

**gh CLI 无法传 token 做自动化**（`gh api` 读取 `GH_TOKEN` 环境变量，但需要先 `gh auth login` 交互式登录）。若只做 repo 创建/commit/push，**直接用 Python requests 调用 GitHub API**，不需要 gh auth。

```python
import urllib.request, urllib.error, json, base64

TOKEN = "ghp_xxxx"  # 用户提供 PAT
headers = {
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# 验证 token
req = urllib.request.Request("https://api.github.com/user", headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    user = json.loads(resp.read())
username = user["login"]  # e.g. "octocat"

# 创建 repo
data = json.dumps({"name": "my-repo", "private": True, "auto_init": True}).encode()
req2 = urllib.request.Request("https://api.github.com/user/repos",
    data=data, headers={**headers, "Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req2) as resp:
        print("created:", json.loads(resp.read())["html_url"])
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    if "already exists" in body.get("message", ""):
        print("repo exists, skip")

# 获取 main 分支 SHA
main_sha = None
for branch in ["main", "master"]:
    r = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/ref/heads/{branch}", headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            main_sha = json.loads(resp.read())["object"]["sha"]
            break
    except urllib.error.HTTPError:
        continue

# 创建 blob → tree → commit → update ref（Git Data API 全流程）
def create_blob(content):
    enc = base64.b64encode(content.encode("utf-8")).decode()
    bd = json.dumps({"content": enc, "encoding": "base64"}).encode()
    req = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/blobs",
        data=bd, headers={**headers, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["sha"]

tree_items = [
    {"path": "README.md", "mode": "100644", "type": "blob",
     "sha": create_blob("# my-repo\n")}
]

tree_data = json.dumps({"tree": tree_items, "base_tree": main_sha}).encode()
req_tree = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/trees",
    data=tree_data, headers={**headers, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req_tree, timeout=15) as resp:
    tree_sha = json.loads(resp.read())["sha"]

commit_data = json.dumps({
    "message": "feat: initial commit",
    "tree": tree_sha,
    "parents": [main_sha] if main_sha else []
}).encode()
req_commit = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/commits",
    data=commit_data, headers={**headers, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req_commit, timeout=15) as resp:
    commit_sha = json.loads(resp.read())["sha"]

# 更新分支
upd = json.dumps({"sha": commit_sha}).encode()
if main_sha:
    req_up = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/refs/heads/main",
        data=upd, headers={**headers, "Content-Type": "application/json"}, method="POST")
else:
    req_up = urllib.request.Request(f"https://api.github.com/repos/{username}/my-repo/git/refs",
        data=json.dumps({"ref": "refs/heads/main", "sha": commit_sha}).encode(),
        headers={**headers, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req_up, timeout=10) as resp:
    json.loads(resp.read())

print("DONE: https://github.com/" + username + "/my-repo")
```

### Token 常见报错
| 错误 | 原因 | 解法 |
|------|------|------|
| `401 Bad credentials` | token 错误/已撤销/scope 不够 | 确认 token 有效且有 `repo` scope |
| `404 Not Found` | repo 不存在或名字拼错 | 先创建 repo（`auto_init: true`） |
| `422 Validation Failed` | 文件路径含非法字符 | 避免中文路径，用英文文件名 |

### GitHub PAT 生成要点
- 地址：https://github.com/settings/tokens/new
- **Scope**：必须勾选 `repo`（整个 repo 分组）
- **Expiration**：建议 30 天
- token 格式：`ghp_` + 36位，或 `github_pat_` + 早期版本
- **生成后立刻复制**，刷新页面不可见

### mcporter + MCP Servers

配置文件：`C:\Users\Administrator\config\mcporter.json`

```json
{
  "mcpServers": {
    "exa":    { "command": "https://mcp.exa.ai/mcp" },
    "weibo":  { "command": "<pip路径>/mcp-server-weibo" },
    "douyin": { "command": "C:\\Program Files\\Python312\\Scripts\\douyin-mcp-server.exe" }
  }
}
```

```bash
mcporter list
mcporter call weibo.search_content --keyword="万科" --limit=5
mcporter call exa.web_search_exa --query "site:mp.weixin.qq.com" --numResults=3
```

gh CLI（`C:\\Program Files\\GitHub CLI\\gh.exe`）仅用于交互式操作（`gh auth login`）。**做自动化脚本用 Python requests 直接调 GitHub API**（见上方 GitHub 自动化一节）。

### GitHub 匿名可用数据

```python
import json, subprocess

# 仓库基本信息
r = subprocess.run(['curl', '-s',
    'https://api.github.com/repos/owner/repo',
    '-H', 'Accept: application/vnd.github.v3+json'],
    capture_output=True, text=True, timeout=15)

# Trending 搜索
r = subprocess.run(['curl', '-s',
    'https://api.github.com/search/repositories',
    '-H', 'Accept: application/vnd.github.v3+json',
    '-G',
    '--data-urlencode', 'q=language:python pushed:>2026-05-19',
    '--data-urlencode', 'sort=stars',
    '--data-urlencode', 'per_page=5'],
    capture_output=True, text=True, timeout=15)

# 用户信息
r = subprocess.run(['curl', '-s',
    'https://api.github.com/users/username',
    '-H', 'Accept: application/vnd.github.v3+json'],
    capture_output=True, text=True, timeout=10)
```

返回值含 `stargazers_count`、`description`、`pushed_at`、`language` 等，无需 token。

## Cookie 导出流程（小红书/抖音）

> **核心原则**：cookie 属于🔴机密级数据，禁止写入 memory 或 output 文件。

需要 cookie 的平台（小红书、抖音）目前没有全自动提取方案。需用户配合导出一次，之后永久复用。

### Step 1：启动 Edge 调试窗口

**⚠️ 必须加 `--remote-allow-origins=*`**，否则 WebSocket 连接返回 403：

```python
import subprocess, time

edge_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
# 杀掉已有 Edge
subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'],
    capture_output=True, text=True, timeout=10)
time.sleep(2)

# 启动调试窗口
subprocess.Popen([
    edge_exe,
    '--remote-debugging-port=9222',
    '--remote-allow-origins=*',
    '--user-data-dir=' + os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\DebugProfile'),
    '--no-first-run',
    '--no-default-browser-check',
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)  # 等端口就绪

# 验证
import urllib.request, json
r = urllib.request.urlopen('http://localhost:9222/json/version', timeout=5)
print(json.loads(r.read().decode()).get('Browser'))
```

### Step 2：用户手动登录

CDP 调试窗口是**独立会话**，不继承已有 Edge 登录态。用户必须在打开的窗口中完成登录。

### Step 3：提取 Cookie（via CDP WebSocket）

```python
import json, urllib.request, websocket

pages = json.loads(urllib.request.urlopen(
    'http://localhost:9222/json', timeout=5).read().decode())
ws = websocket.create_connection(
    pages[0]['webSocketDebuggerUrl'], timeout=10)

# 导航到目标平台
ws.send(json.dumps({'id': 1, 'method': 'Page.navigate',
    'params': {'url': 'https://www.xiaohongshu.com'}}))
time.sleep(8)

# 拿所有 cookies
ws.send(json.dumps({'id': 2, 'method': 'Network.getAllCookies', 'params': {}}))
resp = json.loads(ws.recv())  # 读取响应
cookies = resp.get('result', {}).get('cookies', [])

# 过滤目标域名
target = 'xiaohongshu'  # 或 'douyin'
filtered = [c for c in cookies if target in c.get('domain', '')]
header = '; '.join(f"{c['name']}={c['value']}" for c in filtered)

# 保存到本地（机密文件，禁止上传）
with open(rf'C:\Users\Administrator\{target}_cookie.txt', 'w') as f:
    f.write(header)

ws.close()
```

### Step 4：配置工具

```bash
# 小红书 xhs-cli
xhs login --cookie "$(type C:\Users\Administrator\xiaohongshu_cookie.txt)"

# 抖音 - 写入 mcporter config
# 编辑 C:\Users\Administrator\config\mcporter.json，加入 cookie 字段
```

### Cookie 文件路径规范

| 平台 | 路径 |
|------|------|
| 小红书 | `C:\Users\Administrator\xiaohongshu_cookie.txt` |
| 抖音 | `C:\Users\Administrator\douyin_cookie.txt` |
| Reddit | `C:\Users\Administrator\reddit_cookie.txt` |

**⚠️ 这些文件为🔴机密，禁止上传或写入 memory/wik/output**。

## 安装新渠道

```bash
pip install <package>  # MCP server

# 直接编辑 C:\Users\Administrator\config\mcporter.json 加入 mcpServers 条目
# 避免通过 mcporter.cmd subprocess 调用（PATH 问题）
```

## 相关 skill

- `xhs-sentiment-monitoring`：小红书舆情专项（CDP 浏览器 + 情感分析）
- `windows-env-workflow`：Windows subprocess PATH 问题通用解法
