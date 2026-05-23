# 微信视频号及短视频平台视频下载方案

> 最后更新：2026-05-05 | 调研项目：理想之地竞品视频素材采集

## 方案总览

| 方案 | 难度 | 批量 | 稳定性 | 适合场景 |
|------|------|------|--------|---------|
| **① res-downloader（推荐）** | ⭐ 低 | ✅ 可批量 | 高 | 日常高频采集 |
| ② 微信客户端缓存提取 | ⭐⭐ 中 | ✅ 可批量 | 高 | 不想装第三方工具 |
| ③ 浏览器 DevTools 嗅探 | ⭐⭐⭐ 高 | ❌ 单条 | 中 | 偶尔单条应急 |

---

## 方案一：res-downloader（主推）

### 基础信息

| 项目 | 内容 |
|------|------|
| 仓库 | [putyy/res-downloader](https://github.com/putyy/res-downloader) |
| Star | 17,200+ |
| 最新版 | v3.1.3（2025-12-30） |
| 技术栈 | Go + Wails（跨平台桌面GUI） |
| 许可证 | 开源 |
| 文档 | https://res.putyy.com/ |

### 支持平台

视频号、小程序、抖音、快手、小红书、直播流、m3u8、酷狗音乐、QQ音乐等

### 工作原理

本地代理抓包（MITM）—— 类似 Fiddler/Charles 的图形化版，但做了资源筛选和下载优化：
1. 软件启动本地 HTTP 代理（127.0.0.1:8899）
2. 安装自签名 SSL 证书（解密 HTTPS 流量）
3. 在微信客户端/浏览器打开目标页面 → 流量经过代理
4. 工具嗅探到 video/mp4 等媒体资源 → 展示在界面 → 一键下载

### 下载地址

- **GitHub Releases：** https://github.com/putyy/res-downloader/releases
  - Windows: `res-downloader_3.1.3_win_amd64.exe`（11MB，38,259 下载）
  - Windows ARM: `res-downloader_3.1.3_win_arm64.exe`（11MB，8,573 下载）
  - macOS: `res-downloader_3.1.3_mac.dmg`（16MB，10,131 下载）
  - Linux: 可选 amd64/arm64 二进制或 .deb 包
- **蓝奏云备用（密码：9vs5）：** https://wwjv.lanzoum.com/b04wgtfyb

### 使用步骤

```
① 安装 → 务必允许"安装证书文件" + "允许网络访问"
② 打开软件 → 首页左上角点击"启动代理"
③ 选择要获取的资源类型（默认全部选中即可）
④ 在微信中打开目标视频号视频并完整播放
⑤ 返回软件首页 → 资源列表自动出现 → 勾选/点击下载
⑥ （可选）下载后在操作项点击"视频解密（视频号）"完成解密
```

### 注意事项

- ✅ 17.2k stars，社区验证充分，非恶意软件
- ⚠️ SSL 证书安装是 MITM 代理的必要环节（和 Fiddler/Charles 原理相同），不是后门
- ⚠️ 公司电脑如有 IT 管控，安装自签名证书可能需要管理员权限或 IT 审批
- ❌ 下载的素材仅用于内部竞品洞察和素材参考，禁止二次分发或商业用途

### 常见问题

| 问题 | 解决办法 |
|------|---------|
| 软件无法拦截到资源 | 检查系统代理是否指向 127.0.0.1:8899 |
| 下载慢/大文件失败 | 配合 Neat Download Manager / Motrix 下载 |
| 视频号视频花屏/无法播放 | 右键 → "视频解密（视频号）" |
| 关闭软件后无法上网 | 手动关闭系统代理设置 |
| Win7 兼容 | 下载 v2.3.0 旧版（Electron 版） |
| 更多问题 | https://github.com/putyy/res-downloader/issues |

---

## 方案二：微信客户端缓存提取（无第三方工具）

### 原理

微信 Windows/Mac 客户端播放视频时，会将视频缓存到本地临时目录。

### 操作步骤

1. **电脑端微信**完整播放目标视频号视频（确保缓存写盘）
2. **定位缓存目录：**
   - Windows：`%APPDATA%\Tencent\WeChat\WeChatApplet\` 或 `WeChat Files\[wxid]\FileStorage\Video\YYYY-MM\`
   - 搜索 `*.mp4` 按修改时间倒序排列
3. 视频可能被切分为 `.m4s` 分片 → 使用 WeChatVideoDownloader（GitHub 开源）自动合并

### 优缺点

- ✅ 纯官方客户端操作，不触发风控
- ❌ 需要手动定位文件，分片需要合并工具

---

## 方案三：浏览器 DevTools 嗅探（单条应急）

### 适用条件

视频号链接已分享到微信外部（如复制链接到 Chrome 打开，且未强制跳转微信客户端）。

### 操作步骤

1. Chrome/Edge 打开视频号链接
2. F12 → Network 标签 → 筛选 `video` 或 `mp4`
3. 找到 `Content-Type: video/mp4` 的最大请求
4. 右键 → Open in new tab → 下载

### 局限

- 部分视频号链接有 referer 校验 → 需配合 Video DownloadHelper 扩展
- 页面强制跳转微信客户端时不可用

---

## 场景选型指南（结合理想之地项目）

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 竞品视频号日常监测（批量） | **res-downloader** | GUI 批量操作，解密一体化 |
| 偶尔看一条竞品视频 | 方案二（缓存提取） | 无需额外安装 |
| 调研抖音/小红书竞品素材 | **res-downloader** | 一工具覆盖多平台 |
| 团队内部培训素材库建设 | **res-downloader** + 定时脚本 | 稳定、可批量 |

---

## 与公众号文章抓取（Cloudflare Browser Run）的配合使用

```
公众号文章（文字/图片/政策口径） → Cloudflare Browser Run → Markdown 归档
视频号视频（竞品活动/实景/宣传片）  → res-downloader          → MP4 归档
```

两者互补，覆盖竞品在微信生态内的**所有内容形态**。
