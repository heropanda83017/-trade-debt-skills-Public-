# 微信公众号文章抓取工具对比

## 方案对比总表（2026年5月实地测试）

| 对比维度 | ① Cloudflare Browser Run ✅ 上线 | ② wechat-article-exporter | ③ wechat-download-api |
|---------|-------------------------------|--------------------------|----------------------|
| **核心原理** | Cloudflare边缘网络真实浏览器 | 微信公众平台后台搜索接口 | 微信公众平台后台接口+扫码 |
| **是否需要公众号** | ❌ 不需要 | ✅ 需要一个公众号扫码 | ✅ 需要一个公众号扫码 |
| **单篇文章抓取** | ✅ 完美 | ✅ 支持 | ✅ 支持 |
| **批量历史文章** | ❌ 无法获取列表 | ✅ **核心功能，一键拉取** | ✅ RSS/批量拉取 |
| **RSS自动监控** | ❌ 不支持 | ⚠️ 可配合cron | ✅ **核心功能** |
| **反风控机制** | Cloudflare边缘IP（强） | 微信后台接口（强） | TLS指纹+SOCKS5代理池 |
| **部署难度** | ⭐ 零（只需API Token） | ⭐⭐ 在线站或Docker | ⭐⭐⭐ Docker或Python |
| **安装复杂度** | ✅ 一行curl即可 | ⭐⭐ 扫码登录即可用 | ⭐⭐⭐ 需安装Docker |
| **输出格式** | Markdown/JSON/HTML/截图 | HTML/JSON/Excel/TXT/MD/DOCX | JSON/RSS |
| **评论/阅读量** | ❌ 不支持 | ✅ 支持导出 | ❌ 不支持 |
| **有在线站(0部署)** | ✅ 不需要 | ✅ **https://down.mptext.top** | ❌ 需自部署 |
| **活跃度** | Cloudflare官方维护 | ⭐⭐⭐⭐⭐ 2.3k+ stars | ⭐⭐ 较小 |
| **维护方** | 个人二次封装 | 活跃社区维护 | 个人项目 |
| **费用** | 免费（每天10分钟） | 免费版2个号/付费¥9.9起 | 完全免费 |

## 方案选择指南

### 场景1：只抓一两篇特定文章
→ **Cloudflare Browser Run**（最简，无需扫码登录）

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/browser-rendering/markdown" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"文章链接"}'
```

### 场景2：批量下载某个公众号全部历史文章
→ **wechat-article-exporter**（在线站，最快）

打开 https://down.mptext.top → 扫码登录 → 搜索公众号 → 选择文章 → 导出MD格式 → 下载zip

### 场景3：长期监控公众号更新（RSS订阅）
→ **wechat-download-api**（需自部署Docker或本地运行）

```bash
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data tmwgsicp/wechat-download-api
```
访问 http://localhost:5000 → 扫码 → 搜索想订阅的公众号 → 复制RSS链接 → 接入Feedly/Inoreader

### 场景4：无需部署，零门槛
→ **wechat-article-exporter 在线站**
直接访问 https://down.mptext.top 即可使用，无需任何安装配置。

## 关键发现

### 为什么Cloudflare Browser Run能穿透微信反爬？
传统自动化浏览器（Playwright/Puppeteer/Selenium）自带自动化特征：
- navigator.webdriver = true
- CDP协议特征
- 无头浏览器指纹

Cloudflare Browser Run运行在真实Chrome实例中，无自动化特征，IP来自Cloudflare边缘网络，信誉高。

### wechat-article-exporter 的工作原理
利用微信公众号后台的素材库搜索功能——当你在公众号后台写文章时，可以搜索插入其他公众号的文章。以此接口为基础实现任意公众号文章列表获取。

**优势**：稳定、功能全（支持过滤/合集/评论）
**劣势**：需要有一个微信公众号的管理权限来扫码登录

### wechat-download-api 的核心特性
- 完整的反风控体系：Chrome TLS指纹+SOCKS5代理池+三层限频
- 支持RSS订阅自动轮询
- 登录凭证4天有效期，可配置webhook提醒

## 推荐搭配策略

```
日常快速查 → Cloudflare Browser Run（零配置，单篇秒查）
批量搜刮 → wechat-article-exporter（在线站，下载MD包）
长期监控 → wechat-download-api（Docker，RSS订阅）
```
