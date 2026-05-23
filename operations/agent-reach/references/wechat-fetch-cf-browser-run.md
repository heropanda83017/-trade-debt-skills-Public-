# 微信文章抓取：Cloudflare Browser Run 方案

## 结论

Cloudflare Browser Run API 是抓取微信公众号/微信文章**最可靠**的方案，无需本地浏览器，无需微信 cookie，HTTP 200 直接拿完整 Markdown 内容。

## 方案对比

| 方案 | 依赖 | 成功率 | 维护成本 |
|------|------|--------|---------|
| **CF Browser Run** | CF API token | ~100% | 低 |
| wechat-article-scraper（Cloudflare lib） | Cloudflare SDK | 低（依赖不稳定） | 高 |
| 微信开放平台 API | 企业资质 | 低 | 高 |
| 第三方平台转发 | 第三方 | 不稳定 | 高 |

## 前提

- Cloudflare Account ID：`36c22fb738d187d5ec35f5abfa21dd6c`
- Cloudflare API Token：保存在 profile `.env` → `CLOUDFLARE_API_TOKEN`
- 需要一个真实的微信文章 URL（mp.weixin.qq.com）

## 获取微信文章 URL

微信文章 URL 不规律，无法猜测。用 Exa MCP 语义搜索拿到真实 URL：

```python
# 通过 mcporter exa MCP 搜索
# mcporter call exa.web_search_exa --query "理想之地 site:mp.weixin.qq.com" --numResults 3
```

## 抓取脚本（wechat_fetch.py）

完整脚本存于：`E:\Landofdream\输出\06-脚本\wechat_fetch.py`

核心逻辑：
```python
import os, json, urllib.request, datetime, pathlib, re

# 加载 .env
def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env

env_path = r'C:\Users\Administrator\.hermes\profiles\land-of-dream-planning\.env'
env = load_env(env_path)

account_id = env['CLOUDFLARE_ACCOUNT_ID']
api_token = env['CLOUDFLARE_API_TOKEN']

url = "https://mp.weixin.qq.com/s/Km3oCR8LRiG2opAz7OwYIA"

# CF Browser Run Markdown 端点
api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser_rendering/markdown"
data = json.dumps({"url": url}).encode()
req = urllib.request.Request(api_url, data=data, method='POST')
req.add_header("Authorization", f"Bearer {api_token}")
req.add_header("Content-Type", "application/json")

with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode())

content = result["result"]["markdown"]  # 完整 Markdown
```

## 输出格式

保存到 `E:\Landofdream\wiki\raw\wechat\{date}_{title}.md`，自动附加 Obsidian frontmatter：

```markdown
---
title: 文章标题
source: mp.weixin.qq.com
fetched: 2026-05-22
url: https://mp.weixin.qq.com/s/...
---

正文内容...
```

## 验证结果（2026-05-22）

- 真实文章抓取：HTTP 200，9739 字符，完整内容
- 无需 cookie，无需登录态
- 速度：单篇 < 10s

## wechat-article-scraper skill 评估

skill 里的 Cloudflare SDK 方案（`from cloudflare import Cloudflare`）依赖不稳定。
**推荐直接用 requests + CF REST API**，不要装额外 SDK。

## 局限

- Cloudflare Browser Run 有请求频率限制
- 需要真实的微信文章 URL（无法枚举）
- 部分文章可能因 Cloudflare 检测而返回 403（极少数）
