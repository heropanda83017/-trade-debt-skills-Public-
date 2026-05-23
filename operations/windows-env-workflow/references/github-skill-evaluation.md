# GitHub Skill 评估流程

当用户发来 GitHub 仓库链接询问「这个技能需要吗」时，按以下步骤评估。

## 评估步骤

### Step 1：快速摸底（1 分钟）

```python
import subprocess, json, base64

repo = "owner/repo-name"  # 从 URL 提取

# 仓库元数据
r = subprocess.run(
    ["curl", "-sL", "-H", "Accept: application/vnd.github.v3+json",
     f"https://api.github.com/repos/{repo}"],
    capture_output=True, text=True, timeout=15
)
data = json.loads(r.stdout)
print(f"★{data.get('stargazers_count',0)} | {data.get('language','—')}")
print(f"Desc: {data.get('description','')}")
print(f"平台: {data.get('topics',[])}")
```

### Step 2：读 README

```python
rr = subprocess.run(
    ["curl", "-sL", "-H", "Accept: application/vnd.github.v3+json",
     f"https://api.github.com/repos/{repo}/readme"],
    capture_output=True, text=True, timeout=15
)
rdata = json.loads(rr.stdout)
readme = base64.b64decode(rdata.get("content","")).decode("utf-8", errors="replace")
print(readme[:2000])
```

### Step 3：看目录结构

```python
rc = subprocess.run(
    ["curl", "-sL",
     f"https://api.github.com/repos/{repo}/contents/"],
    capture_output=True, text=True, timeout=15
)
items = json.loads(rc.stdout)
for item in items:
    print(f"  [{item['type']:>4}] {item['name']}")
```

### Step 4：读 SKILL.md（如果存在）

```python
rs = subprocess.run(
    ["curl", "-sL",
     f"https://raw.githubusercontent.com/{repo}/refs/heads/main/SKILL.md"],
    capture_output=True, text=True, timeout=15
)
print(rs.stdout[:3000])
```

## 评估决策树

```
这个 skill 对我们有用吗？

├── 平台兼容？
│   ├── 明确写了支持 Hermes / Nous Agent ✅
│   ├── 写支持 Claude Code / Cursor / Codex / Gemini CLI ❌（平台不兼容）
│   └── 什么都没写 ❌（风险太高）
│
├── 使用场景相关？
│   ├── 营销/运营/数据分析/知识管理 ✅
│   ├── 编程/代码生成/软件部署 ❌（场景不搭）
│   └── 多功能/元技能 → 看实际用途是否对我们 ✅
│
├── 部署复杂度可接受？
│   ├── 需要 Node.js / npm → 确认是否有 Python 等效方案
│   ├── 需要跑服务器/数据库 → 本地无法部署则不用
│   └── 纯本地 Python 脚本 → ✅
│
└── 隐私/安全
    ├── 持续监听 session（Skill Factory 模式）→ 国企场景 ❌
    └── 被动工具（按需调用）→ ✅
```

## 典型决策案例

| hermes-cloudflare | — | ✅ 安装 | Hermes 原生插件，Browser Rendering，支持 cf_markdown/crawl/scrape 等 |

| Skill | Star | 结论 | 原因 |
|-------|------|------|------|
| agenticskills find-skills | — | ❌ | 平台不兼容（claude-code/codex/cursor），无 Hermes |
| vercel-labs agent-skills | 26,954 | ❌ | 全是前端/Vercel 专属，零通用性 |
| skill-factory | 324 | ❌ | 平台不兼容 + 持续监听 session 有隐私风险 |
| execplan | 39 | ❌ | 纯编程任务场景，不适合营销运营 |
| agent-browser (Rust) | 33,957 | ❌ | 需要 Rust 工具链，Hermes 不支持 |
此法完全绕开 Git，不受 gitconfig 影响。适合所有从 GitHub 下载仓库的场景。

## hermes-cloudflare 插件安装要点

hermes-cloudflare 插件装好后，**需要 Cloudflare 凭证才能使用**，不需要时不装也行。

安装步骤（Windows，绕过 gitconfig 循环问题）：
1. Python zip 下载：`urllib.request.urlretrieve('https://github.com/raulvidis/hermes-cloudflare/archive/refs/heads/main.zip', tmp_zip)`
2. 解压后复制 `hermes-cloudflare-plugin/` → `~/.hermes/plugins/hermes-cloudflare/`
3. pip install httpx
4. 配置环境变量：`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`

凭证获取：Cloudflare Dashboard → API Tokens → Create Custom Token → Browser Rendering - Edit 权限。

## 常见陷阱

**JSON NoneType 错误：**
```python
# 错误（license 字段有时为 None）
data.get('license',{}).get('spdx_id','none')  # NoneType has no .get()

# 正确
lic = data.get('license') or {}
print(lic.get('spdx_id', 'none'))
```

**README 路径：**
- `raw.githubusercontent.com` 的分支名必须准确（`main` vs `master`）
- 用 API 返回的 `default_branch` 字段更可靠

## 评估完成后

向用户说明：
1. **结论**（需要 / 不需要）
2. **原因**（平台兼容 / 场景相关 / 部署复杂度）
3. **如果需要，具体怎么装**（如果适用）
