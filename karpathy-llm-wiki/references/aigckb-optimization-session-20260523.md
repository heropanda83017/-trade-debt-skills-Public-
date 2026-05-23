# AIGC-KB 优化实战记录（20260523）

## 背景

2026年5月23日，对 E:\AIGC-KB\wiki\（学习笔记 vault）进行了系统性优化。这是该 vault 首次大型养护。

## 初始状态

- 60 个 .md 文件分布在 9 个子目录 + root
- 目录编号杂糅：包含 00-inbox（废弃）、04-applications（已删除）、01-theory 和 01-foundations（重复编号）
- 部分页面字数极少（<500字），内容太薄
- 部分主题重复：三篇数学基础、两篇相似目录名

## 执行过程

### 第一阶段：目录结构重排

将 9 个目录规范为 01-08：

| 编号 | 名称 | 变更 |
|------|------|------|
| 00-inbox | 废弃 | 删除（无实质内容） |
| 01-theory | 理论概况 | 保留，接收推荐渠道内容 |
| ~~01-foundations~~ | → 02 | 重编号 |
| 02-fundamentals | 基础 | 保留（已合并10→3） |
| 03-core-ai | 核心AI | 保留（新增顺序导航链接） |
| 04-tools | 工具 | 保留待继续优化 |
| ~~04-applications~~ | 废弃 | 删除（空目录） |
| 05-applications | 应用 | 保留（含圈层运营+量化） |
| 06-reading-notes | 读书笔记 | 保留 |
| 07-practices | 实战笔记 | **新增**（学习闭环产出） |
| 08-investment | AI投资研究 | 保留 |

### 第二阶段：02-fundamentals 合并

从 10 页压缩为 3 页：

| 原始文件 | 操作 | 目标 |
|---------|------|------|
| python-环境搭建.md | 合并 | python环境搭建与基础概念.md |
| python-基础概念.md | 合并 | ↑ |
| python-基本语法.md | 合并 | ↑ |
| python常用库-numpy.md | 合并 | python科学计算库.md |
| python常用库-pandas.md | 合并 | ↑ |
| python常用库-SymPy.md | 合并 | ↑ |
| 线性代数基础.md | 合并 | 数学基础.md |
| 微积分基础.md | 合并 | ↑ |
| 概率论基础.md | 合并 | ↑ |
| 蒙特卡洛模拟.md | 保留单独 | （特殊主题，暂不合并） |

### 第三阶段：03-core-ai 链接增强

4 篇核心 AI 笔记（56页→4页）新增顺序导航：
- 人工神经网络概念整理.md → 底部：下一步看 CNN
- CNN概念整理.md → 底部：下一步看 Transformer
- Transformer概念整理.md → 底部：下一步看 Agent
- Agent工具调用与系统设计.md → 底部：到达终端

### 第四阶段：实战笔记新增

新建 4 篇实战笔记到 07-practices：

| 文件名 | 内容概要 |
|--------|---------|
| hermes-agent-workflow-patterns.md | Hermes Agent 五种工作模式、多Agent协作 |
| rag-wiki-knowledge-retrieval.md | Wiki检索+RAG实操（含读取/搜索/向量化） |
| agent-tool-calling-patterns.md | Agent工具调用模式（批量/异步/prompt技巧） |
| prompt-engineering-gov-doc-and-opinion.md | 国企公文Prompt工程（多角色配置/SOUL.md驱动） |

每种模式=学概念→真实用过→写笔记。

### 第五阶段：跨目录合并（待执行）

| 源文件 | 目标 | 理由 |
|--------|------|------|
| 04-tools/AI学习推荐渠道.md → 01-theory/ | 合入学习路径 | 路径讲顺序，渠道讲来源，互补 |
| 04-tools/RAG原理与学习路径.md → 07-practices/ | 合入 RAG 实战笔记 | 理论+实战合并为一本通 |

## 关键经验

1. **学习笔记 vault ≠ 项目 vault**：项目 wiki 要靠 wikilink 连接成网；学习笔记靠目录+文件名定位，孤立页面正常
2. **先审阅再动手**：扫描完 60 页后判断那些是该删除的、合并的、保留的，比边做边想要快
3. **实战笔记是学习闭环的最后一步**：学概念→项目里用一次→固化到 07-practices，不做这三步等于没学
4. **编号重排要谨慎**：删除目录后留下空缺（04-applications 删掉后 05-08 自动递补），需要手动重编号并在 index.md 同步更新
