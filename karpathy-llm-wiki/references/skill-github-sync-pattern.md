# Skill → GitHub 同步模式（API 直推）

当 `git` CLI 不可用（如 MSYS git-bash 无法访问 Windows 路径）时，可通过 GitHub API 直推技能更新。

## 适用场景

- `skill_manage patch` 已更新本地 skill 文件（`~/.hermes/.../skills/<name>/SKILL.md`）
- 需要同步到 GitHub 仓库（`heropanda83017/<skill-name>`）
- `git clone/push` 因环境限制不可用

## 工作流

### Step 1：获取 GitHub Token

从 `~/.hermes/.env` 读取 `GITHUB_PAT`。该变量已在 .env 中配置，无需手动输入。

### Step 2：读取本地更新后的 SKILL.md

```python
import os
local_skill = os.path.expanduser('~/.hermes/profiles/land-of-dream-planning/skills/<name>/SKILL.md')
with open(local_skill, 'r', encoding='utf-8') as f:
    new_content = f.read()
```

### Step 3：获取当前文件 SHA（GitHub API 要求）

```python
import json, base64, urllib.request

pat = os.environ.get('GITHUB_PAT')  # 或从 .env 读取
url = f'https://api.github.com/repos/heropanda83017/<skill-name>/contents/SKILL.md'

req = urllib.request.Request(url)
req.add_header('Authorization', f'token {pat}')
req.add_header('Accept', 'application/vnd.github.v3+json')

with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())
    sha = data['sha']  # 用于 Step 4 的 PUT 请求
```

### Step 4：推送更新

```python
new_encoded = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')

payload = json.dumps({
    'message': '<commit-message>',
    'content': new_encoded,
    'sha': sha,
    'branch': 'main'
}).encode('utf-8')

req2 = urllib.request.Request(url, data=payload, method='PUT')
req2.add_header('Authorization', f'token {pat}')
req2.add_header('Accept', 'application/vnd.github.v3+json')
req2.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req2, timeout=15) as resp:
    result = json.loads(resp.read())
    commit_sha = result['commit']['sha']
```

### Step 5：如果连续推送两次（changelog 更新等）

每次推送后 SHA 会变化，第二次推送前必须重新获取 SHA：

```python
# 重新获取（不能在原变量上复用）
with urllib.request.urlopen(urllib.request.Request(url, headers={
    'Authorization': f'token {pat}',
    'Accept': 'application/vnd.github.v3+json'
}), timeout=15) as resp:
    sha = json.loads(resp.read())['sha']

# 然后再用新 SHA 做第二次 PUT
```

## 注意事项

| 坑 | 说明 |
|----|------|
| SHA 会变 | 每次 commit 后 SHA 更新，连续 push 需重新 GET |
| Token 不过期 | GITHUB_PAT 是 personal access token，不过期 |
| 文件名必须正确 | 仓库目录结构不同时，调整 `contents/` 后的路径 |
| base64 编码 | 内容需 base64 编码（标准库 base64.b64encode） |
| 默认分支 | 确认仓库默认分支（通常是 main 或 master） |

## 参考

2026-05-23 实战：`meeting-minutes` skill v2.4 更新（两次 commit：第一次 feat 内容更新，第二次 docs changelog），均通过 API 直推，无需本地 git。
