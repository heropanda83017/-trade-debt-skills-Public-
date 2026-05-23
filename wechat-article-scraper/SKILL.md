---
name: wechat-article-scraper
description: 微信生态内容获取工具集 — 涵盖微信公众号文章（Cloudflare Browser Run）与微信视频号视频（本地代理工具）的抓取/下载/归档方案。可穿透微信反爬限制，提取文章全文Markdown或下载视频号视频资源，归档到项目知识库。
version: 1.3.0
dependencies:
  - CLOUDFLARE_API_TOKEN
  - CLOUDFLARE_ACCOUNT_ID
  - httpx
trigger: 用户提供微信公众号文章链接、要求学习公众号内容、或询问如何下载微信视频号/抖音/小红书等视频资源、或询问如何从下载的视频中提取文字/字幕/语音转文字
references:
  - references/cloudflare-browser-run-setup.md — Cloudflare Browser Run API 配置、令牌权限、故障排查
  - references/tools-comparison.md — 三种公众号文章抓取工具对比（CF Browser Run / wechat-article-exporter / wechat-download-api），含场景选型指南
  - references/video-downloading.md — 视频号/抖音/快手等短视频平台视频下载方案，主推 res-downloader 工具使用指南
  - references/res-downloader-deployment.md — res-downloader 的 WSL→Windows 部署安装指南（GitHub下载、SHA256校验、目录结构、桌面快捷方式创建）
  - references/voice-to-text.md — 视频语音转文字方案，含 Buzz/Faster-Whisper/FunASR 等工具对比、部署指南、完整工作流
  - references/output-directory-convention.md — Hermes正式成果文件输出目录规范（E:\\\\Hermes）
---

# 微信生态内容获取工具集

**适用范围：** 微信公众号文章（Markdown全文） + 微信视频号视频（mp4下载） + 抖音/快手/小红书等短视频平台

## 分支一：微信公众号文章抓取（Cloudflare Browser Run）

### 前置条件

- `CLOUDFLARE_ACCOUNT_ID` 环境变量已配置
- `CLOUDFLARE_API_TOKEN` 环境变量已配置（**必须**含 `Browser Rendering - Edit` 权限，仅 `Workers - Edit` 权限不够）
- `httpx` Python库已安装
- Hermes记忆系统正常运行

## 核心发现：反爬突破

微信公众号对传统自动化浏览器（Playwright/Puppeteer/Selenium/Headless Chrome）有严格的检测机制，所有本地自动化工具访问均返回"环境异常"验证页面。
**Cloudflare Browser Run 可以穿透此限制**，因为它运行在 Cloudflare 边缘网络的真实浏览器上，IP信誉高，不会被微信判定为异常。

| 访问方式 | 微信公众号 | 小红书 | 百度 |
|---------|-----------|-------|-----|
| 本地agent-browser/Playwright | ❌ 环境异常 | ❌ IP风险 | ❌ 验证码 |
| **Cloudflare Browser Run** | ✅ **可穿透** | ⚠️ 待测试 | ⚠️ 待测试 |

## API端点选择指南

| 端点 | 用途 | 速度 | 内容完整性 | 适用场景 |
|------|------|------|-----------|---------|
| `/browser-rendering/markdown` | 文章全文Markdown | ⭐⭐⭐ 快(~3-8s) | ⭐⭐⭐ 含正文+封面+日期 | **首选：需阅读全文内容** |
| `/browser-rendering/content` | 完整渲染HTML（含JS） | ⭐⭐ 中(~8-20s) | ⭐⭐⭐⭐⭐ 含所有JS变量+额外链接 | **高级：需提取__biz/gh_id/更多链接** |
| `/browser-rendering/screenshot` | 页面截图 | ⭐⭐⭐ 快(~3-8s) | ⭐⭐ 仅视觉 | 备份存档、页面还原 |
| `/browser-rendering/scrape` | CSS选择器提取 | ⭐⭐⭐ 快(~3-8s) | ⭐⭐ 指定元素 | 精确提取特定区域 |

## 公众号信息提取技术

### 从单篇文章提取公众号信息

通过 `content` 端点获取完整HTML后，可从页面JavaScript变量中提取：

```python
import re

def extract_account_info(html_text: str) -> dict:
    """从公众号文章HTML中提取账号信息"""
    info = {}
    
    # __biz（Base64编码的公众号唯一标识）
    biz_match = re.search(r'biz\s*:\s*["\']([^"\']+)["\']', html_text)
    if biz_match:
        info['__biz'] = biz_match.group(1)
    
    # gh_id（公众号的gh_开头的ID）
    gh_match = re.search(r'gh_[a-f0-9]{12}', html_text)
    if gh_match:
        info['gh_id'] = gh_match.group()
    
    # 公众号名称
    name_match = re.search(r'[\"\'](?:nickname|nick_name|NickName)[\"\']\s*[:=]\s*[\"\']([^\"\']+)[\"\']', html_text)
    if name_match:
        info['nickname'] = name_match.group(1)
    
    # 头像URL
    avatar_match = re.search(r'[\"\']headimg_url[\"\']?\s*[:=]\s*[\"\']([^\"\']+)[\"\']', html_text)
    if avatar_match:
        info['avatar'] = avatar_match.group(1)
    
    return info
```

### 从文章内发现更多文章

`content` 端点返回的HTML中可能包含其他文章链接。搜索方法：

```python
article_links = set(re.findall(
    r'https?://mp\.weixin\.qq\.com/s/[a-zA-Z0-9_-]+', 
    html_text
))
# 过滤掉当前文章链接
article_links.discard(current_url)
```

### 公众号历史文章主页

格式：`https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={__biz}#wechat_redirect`

**注意**：此页面需要微信客户端认证，通过API直接访问会返回"Open link in Weixin"，无法绕过。只能通过发现单个文章链接的方式逐个抓取。

## 使用场景

| 场景 | 触发方式 | 效果 |
|------|---------|------|
| 抓取单篇公众号文章 | 用户提供 `mp.weixin.qq.com/s/xxx` 链接 | 提取全文Markdown，分析核心要点，归档到项目知识库 |
| 批量学习多篇文章 | 用户提供多个链接或截图+链接 | 逐篇提取并综合对比分析 |
| 定时监控公众号更新 | 配合cronjob定时任务 | 定期检查公众号文章更新并自动归档 |

## API用法

### 1. 抓取文章为Markdown（推荐，结构最完整）

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/browser-rendering/markdown" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "公众号文章链接", "gotoOptions": {"waitUntil": "networkidle0"}}'
```

返回结果中的 `result` 字段即为文章Markdown全文。

### 2. 截图保存文章

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/browser-rendering/screenshot" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "公众号文章链接"}' \
  --output "article-screenshot.png"
```

### 3. 抓取文章内容（完整渲染HTML，含JS变量）

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/browser-rendering/content" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "公众号文章链接", "gotoOptions": {"waitUntil": "load"}}'
```

**注意**：`content` 端点返回的HTML可能非常大（单篇文章可达3-4MB），包含完整JS、CSS和渲染后的DOM。

## Python调用脚本（推荐在execute_code中使用）

```python
import json, os, httpx, re

def fetch_wechat_article(url: str) -> dict:
    """通过Cloudflare Browser Run API抓取微信公众号文章全文"""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    
    if not account_id or not token:
        return {"success": False, "error": "Cloudflare环境变量未配置"}
    
    api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/markdown"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"url": url, "gotoOptions": {"waitUntil": "networkidle0"}}
    
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(api_url, headers=headers, json=payload)
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_wechat_markdown(markdown_text: str) -> dict:
    """解析微信公众号文章Markdown，提取结构化信息"""
    result = {}
    
    # 提取标题
    title_match = re.search(r'^# (.+)$', markdown_text, re.MULTILINE)
    result['title'] = title_match.group(1).strip() if title_match else "未识别标题"
    
    # 提取发布时间（多个格式）
    for fmt in [
        r'_(\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{2})_',
        r'_(\d{4}-\d{2}-\d{2} \d{2}:\d{2})_',
    ]:
        m = re.search(fmt, markdown_text)
        if m:
            result['publish_date'] = m.group(1)
            break
    if 'publish_date' not in result:
        result['publish_date'] = "未识别时间"
    
    # 提取封面图
    cover_match = re.search(r'!\[cover_image\]\((.+?)\)', markdown_text)
    result['cover_image'] = cover_match.group(1) if cover_match else ""
    
    return result

def extract_account_info(html_text: str) -> dict:
    """从公众号文章HTML中提取账号信息"""
    info = {}
    
    # __biz
    biz_match = re.search(r'biz\s*:\s*["\']([^"\']+)["\']', html_text)
    if biz_match:
        info['__biz'] = biz_match.group(1)
    
    # gh_id
    gh_match = re.search(r'gh_[a-f0-9]{12}', html_text)
    if gh_match:
        info['gh_id'] = gh_match.group()
    
    # 公众号名称
    name_match = re.search(r'[\"\'](?:nickname)[\"\']\s*:\s*[\"\']([^\"\']+)[\"\']', html_text)
    if name_match:
        info['nickname'] = name_match.group(1)
    
    return info
```

## 输出目录

正式成果文件（文章归档、分析报告、摘要JSON）统一保存到 `E:\Hermes\` 对应子目录（WSL路径：`/mnt/e/Hermes/`），不要保存在 WSL home 目录。详见 `references/output-directory-convention.md`。

## 工作流程

```
用户提供微信公众号文章链接
    ↓
① 通过Cloudflare Browser Run API抓取Markdown全文（/browser-rendering/markdown）
    ↓
② 解析提取：标题、发布日期、封面图、正文
    ↓
③ 核心内容提炼：活动信息、政策口径、配套进展、官方表述
    ↓
④ 归档到项目记忆库（memory工具）
    ↓
⑤ （可选）通过content端点获取完整HTML，提取__biz/gh_id
    ↓
完成 —— 后续所有输出自动匹配官方口径

---

## 分支二：微信视频号/短视频平台视频下载（本地代理工具）

详见 `references/video-downloading.md`（使用指南）和 `references/res-downloader-deployment.md`（WSL→Windows部署安装），主推工具：

| 工具 | 仓库 | 评分 | 适用场景 |
|------|------|------|---------|
| **res-downloader** | putyy/res-downloader | ⭐⭐⭐ 17.2k stars | **首选**：视频号/抖音/快手/小红书，GUI操作 |
| 微信缓存提取 | 手动操作 | ⭐⭐ | 无需装软件，适合单条 |
| 浏览器DevTools | 无需工具 | ⭐ | 应急单条 |

## 成本控制

- Workers Free计划每日赠送 **10分钟** 浏览器时间
- 单次markdown请求约3-8秒，每日可免费抓取约 **75-200篇文章**
- Workers Paid计划每月赠送 **10小时**，超出部分$0.09/小时
- 每次请求返回的 `X-Browser-Ms-Used` HTTP头包含毫秒级耗时

## 故障排查对照表

| 问题 | 可能原因 | 解决 |
|------|---------|------|
| HTTP 403 / Authentication error | Token缺少Browser Rendering权限 | 重新创建Token，选择"浏览器渲染 - 编辑"权限 |
| HTTP 10000 Authentication error | Token无效/过期 | 到Cloudflare后台重新生成Token |
| 返回"Open link in Weixin" | 访问了需微信客户端认证的页面 | 仅访问 `mp.weixin.qq.com/s/xxx` 单篇文章链接 |
| 返回"环境异常" | 非Cloudflare API调用方式 | 确保使用 `/browser-rendering/` 端点，不是本地工具 |
| 连接超时 | 网络问题或页面加载慢 | 添加 `gotoOptions: {waitUntil: "load"}` 而非 `networkidle0` |
| HTML内容3-4MB | content端点返回完整渲染DOM | 这是正常行为，markdown端点内容约3-6KB |
| 搜狗微信搜索返回空 | 搜狗公众号搜索索引不完整 | 改用Bing搜索 `site:mp.weixin.qq.com 公众号名` |

## 已验证的测试结果

| 测试项目 | 结果 |
|---------|------|
| 公众号：武汉理想之地（mp.weixin.qq.com/s/xxx） | ✅ 穿透成功，完整获取全文 |
| 文章标题、日期提取 | ✅ 正常 |
| __biz提取（从HTML JS变量） | ✅ 正常（如 `MzkzODkzMzQxMg==`） |
| gh_id提取 | ✅ 正常（如 `gh_6119c0e94741`） |
| 历史文章列表页访问 | ❌ 需微信客户端认证 |
| 搜狗微信搜索 | ❌ 部分公众号无法索引 |
