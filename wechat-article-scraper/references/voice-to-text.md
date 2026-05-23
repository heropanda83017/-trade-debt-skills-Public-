# 视频语音转文字方案（Voice-to-Text Pipeline）

> 最后更新：2026-05-05 | 调研场景：理想之地竞品视频素材文字提取
> 前置工具：res-downloader（下载视频号/抖音/小红书视频）→ 本方案（提取文字）→ 竞品策略分析

## 方案总览

| 工具 | ⭐ Stars | GUI？ | 中文识别 | 速度 | 推荐指数 |
|------|---------|-------|---------|------|---------|
| **Buzz** 🥇 | 19.1k | ✅ Windows 桌面版 | ✅ 好 | 中等 | ⭐⭐⭐ 首选 |
| **Faster-Whisper** 🥈 | 22.6k | ❌ 命令行 | ✅ 好 | **快4倍** | ⭐⭐⭐ 批量 |
| **WhisperX** 🥉 | 21.7k | ❌ 命令行 | ✅ 好 | 快+词级时间戳 | ⭐⭐ 精确 |
| **FunASR** | 16.0k | ❌ 命令行 | ✅ **中文最佳** | 快 | ⭐⭐ 高精度 |
| OpenAI Whisper | 98.9k | ❌ 命令行 | ✅ 好 | 慢（基准线） | ⭐⭐ 生态最大 |
| whisper.cpp | 49.4k | ❌ 命令行 | ✅ 好 | 极快（CPU优化） | ⭐⭐ 低配机器 |
| Subtitle Edit | 12.8k | ✅ Windows 桌面版 | ⚠️ 较弱 | 取决于引擎 | ⭐⭐ 字幕编辑 |
| sherpa-onnx | 12.0k | ❌ 命令行 | ✅ 好 | 极快 | ⭐ 嵌入式场景 |
| Vosk | 14.7k | 部分有 | ✅ 好 | 快 | ⭐ 离线轻量 |

---

## 🥇 首选推荐：Buzz

### 为什么是 Buzz

- **有完整 Windows 桌面 GUI**，下载即装，无需命令行
- 底层基于 OpenAI Whisper 模型（`large-v3` 中文准确率极高）
- **完全离线运行**（模型首次下载后断网可用）
- 支持导出 TXT / SRT / VTT / JSON 等多种格式
- 可直接拖入视频或音频文件，操作极简

### 下载安装

**最新版：** v1.4.4（2026-03-14 发布）

```bash
# GitHub Release 下载 Windows 安装包（4.3MB 在线安装器）
# 或 https://sourceforge.net/projects/buzz-captions/files/ 下载完整离线包
curl -L -o Buzz-1.4.4-windows.exe \
  "https://github.com/chidiwilliams/buzz/releases/download/v1.4.4/Buzz-1.4.4-windows.exe"
```

**SHA256 校验（v1.4.4 windows.exe）：**
```
863e9a0afd19decb8ed7a46877773e2f8f335efbef4ea7353d1834285545591d
```

### 使用流程

```
① 安装 Buzz
② 选择 Whsiper 模型（推荐 fine-tuned large-v3 或 medium，中文效果好）
   → 模型首次需下载（large-v3 约 3GB，medium 约 1.5GB）
③ 拖入视频/音频文件（支持 mp4 / m4a / mp3 / wav 等）
④ 语言选 Chinese
⑤ 点击 Transcribe 开始识别
⑥ 导出 → TXT 纯文本 / SRT 字幕 / VTT
```

### 模型选型指南

| 模型 | 大小 | 中文精度 | 速度 | 适用场景 |
|------|------|---------|------|---------|
| `tiny` | ~150MB | 差 | 极快 | 测试/预览 |
| `base` | ~300MB | 一般 | 快 | 快速粗筛 |
| `small` | ~500MB | 中等 | 中等 | 一般场景 |
| `medium` | ~1.5GB | 好 | 较慢 | **推荐：日常使用** |
| `large-v3` | ~3GB | **最好** | 慢 | **推荐：精度优先/竞品分析** |

---

## 🥈 批量场景推荐：Faster-Whisper

### 适用场景

- 需要批量处理大量竞品视频（10+ 条/天）
- 能接受命令行操作
- 对处理速度有要求

### 优势

- 基于 CTranslate2 优化，**比原版 Whisper 快 4 倍**
- 内存占用更低
- 识别精度无损失

### 安装（Windows 需要 Python 环境）

```bash
pip install faster-whisper

# 基本用法
whisper-ctranslate2 video.mp4 --model large-v3 --language zh --output_dir ./output
```

---

## 🥉 中文精度最优：FunASR

### 适用场景

- 视频内容包含大量**中文专业术语**（房地产术语、政策表述）
- 对识别准确率有极端要求
- 能接受较复杂的部署

### 优势

- 阿里达摩院出品，中文语音识别领域**业界标杆**
- 对中文口音、专业术语、噪声环境下表现优于 Whisper
- 支持标点恢复、VAD（语音活动检测）

### 安装部署

```bash
pip install funasr
```

---

## 完整工作流（与 res-downloader 衔接）

```
竞品视频号/抖音/小红书
       ↓
res-downloader（本地代理抓包）
       ↓ 输出 .mp4
┌──────────────────┐
│  D:\res-downloader\  │
└──────────────────┘
       ↓
Buzz（拖入视频 → 选中文 → Transcribe）
       ↓ 输出 .txt / .srt
┌──────────────────┐
│  D:\Buzz\            │
└──────────────────┘
       ↓
竞品说辞/策略/话术分析
       ↓ 归档到 E:\Hermes\03-竞品分析\
```

---

## 注意事项

1. **离线模型存储位置：** Buzz 的模型缓存默认在 `C:\Users\<用户名>\.cache\whisper\`，会占用 1.5-3GB 空间
2. **GPU 加速：** 如果有 NVIDIA 显卡，Buzz 会自动使用 CUDA 加速；无独显则用 CPU 较慢（large-v3 处理 10 分钟视频约需 15-20 分钟）
3. **背景音乐干扰：** 微信视频号的视频常有背景音乐或环境音，Whisper 系列对此有一定抗噪能力，FunASR 表现更佳
4. **竞品分析建议：** 提取文字后，重点关注竞品的**话术结构、价值主张、价格锚定、学区/配套输出策略**
5. **合规红线：** 下载的视频素材和提取的文字**仅限内部竞品分析使用**，禁止二次分发或公开引用
