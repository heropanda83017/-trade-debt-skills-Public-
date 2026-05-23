# GitHub API 直推文件：contents API vs blobs API

## 核心教训

空 repo（`auto_init: False` 创建）使用 `POST /git/blobs` 会返回 **409 Conflict**：
```
Git Repository is empty.
```

解决：改用 **PUT /repos/{owner}/{repo}/contents/{path}** API（contents API）。

## contents API 完整流程

```python
import urllib.request, urllib.error, json, base64

TOKEN = "ghp_xxxx"
headers = {
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json"
}

def do(method, url, data=None):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read())

def upload_contents(repo, path, content, msg="add file"):
    """上传单个文件到 repo（自动处理 sha 更新）"""
    enc = base64.b64encode(content.encode("utf-8")).decode()
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{path}"

    # GET 获取已存在文件的 sha（更新时必须）
    r_get, _ = do("GET", url)
    body = {"message": msg, "content": enc}
    if r_get and "sha" in r_get:
        body["sha"] = r_get["sha"]

    req = urllib.request.Request(url,
        data=json.dumps(body).encode(),
        headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read())

def ensure_repo_public(repo_name):
    """确保 repo 存在且为 public"""
    # 1. 创建（私有或无初始化）
    _, err = do("POST", "https://api.github.com/user/repos",
        json.dumps({"name": repo_name, "private": False,
                    "auto_init": False}).encode())
    if err and "already exists" not in err.get("message", ""):
        print(f"创建失败: {err}")

    # 2. 改为 public
    do("PATCH", f"https://api.github.com/repos/{username}/{repo_name}",
       json.dumps({"private": False}).encode())

def publish_skill(repo_name, skill_dir, desc):
    """发布整个 skill 目录到 GitHub"""
    ensure_repo_public(repo_name)

    for root, dirs, filenames in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', '.hub')]
        for fname in filenames:
            if fname.endswith('.pyc'): continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, skill_dir).replace(os.sep, '/')
            with open(fpath, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            r, err = upload_contents(repo_name, rel, content)
            print(f"{'✓' if r else '✗'} {rel}")
            if err:
                print(f"  → {err.get('message', err)[:80]}")

    # README
    r2, _ = upload_contents(repo_name, "README.md",
        f"# {repo_name}\n\n{desc}\n\nSee SKILL.md\n", "docs: add README")
```

## 两种 API 的适用场景

| 场景 | API | 原因 |
|------|-----|------|
| 空 repo 或批量上传多个文件 | `PUT /contents` | 不依赖 git ref，`sha` 更新自动处理 |
| 已有很多文件的 repo，追加文件 | `POST /blobs` + `POST /trees` + `POST /commits` | 避免多次网络往返，更高效 |
| 更新已存在文件 | `PUT /contents`（必须带 `sha`） | `blobs` API 无此功能 |

## Token 验证

首次使用前先验证 token：
```python
req = urllib.request.Request("https://api.github.com/user", headers=headers)
with urllib.request.urlopen(req) as resp:
    user = json.loads(resp.read())
username = user["login"]  # "heropanda83017"
```

401 Unauthorized 常见原因：
1. Token 复制错误（字符缺失/多余）—— 重新生成
2. Scope 不够——需含 `repo`（创建仓库）或 `gist`（仅 gist）
3. Token 已撤销——重新生成

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 409 Conflict on blobs | 空 repo | 用 contents API |
| 401 Unauthorized | Token 无效/过期 | 重新获取 |
| 422 name already exists | repo 已存在 | 跳过创建或改名为 unique name |
| 403 Forbidden | Token 权限不足 | 确认勾选了 repo scope |
| 文件内容乱码 | 编码问题 | `encoding='utf-8', errors='ignore'` |
