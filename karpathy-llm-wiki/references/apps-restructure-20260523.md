# 05-applications 目录瘦身实战记录（2026-05-23）

## 背景

对 `E:\AIGC-KB\wiki\05-applications` 进行结构性重组。该目录包含两类内容：
- **社区运营**：13 个活动案例 + 模板 + 经验笔记 + RAG 配置（17 个散文件）
- **量化研究**：1 篇实战 + 4 篇课程笔记（5 个文件）

## 初始状态

```
05-applications/
├── applications-agent/           ← 空目录（删除）
├── applications-business/
│   └── ai-driven-community-operation/
│       ├── README.md
│       ├── RAG配置说明.md
│       ├── case-studies/         ← 13个散文件，每篇300-470字
│       ├── practices/            ← 1个文件（636字）
│       └── templates/            ← 1个文件（265字）
└── applications-quant/
    ├── 成长因子的选股策略.md      ← 实战（保留）
    ├── 迪哥AI-金融量化-* ×4      ← 课程笔记（迁移）
```

## 执行过程

### 1. 创建合集：圈层活动案例集.md

将 13 个散文件合并为一个文档：
- 顶部：分类索引表（含核心亮点列）
- 主体：每个案例转为 `## [标题]` 二级标题，保留全部原始内容
- 共 5,662 字，原 13 文件合计约 4,800 字（合并后因索引表略有增长）

### 2. 目录瘦身

| 旧目录 | 操作 | 结果 |
|--------|------|------|
| templates/（圈层活动案例模板.md） | 合入 README.md | 目录删除 |
| practices/（圈层运营核心经验总结.md） | 合入 README.md | 目录删除 |

### 3. README 重写

新 README 结构：
- 文件结构表（仅 3 行：合集 / RAG配置 / 本文件）
- 活动案例模板（原 templates/ 内容）
- 圈层运营核心经验（原 practices/ 内容，含成功经验/踩坑/优化方向）
- 沉淀规范

### 4. 课程笔记归位

4 篇「迪哥AI-金融量化-」文件移至 06-reading-notes/课程笔记 子节。

### 5. 空目录删除

applications-agent/（空）直接删除。

### 6. index.md 同步更新

- 05-applications：10 行→4 行（README + 合集 + RAG + 量化）
- 06-reading-notes：新增「课程笔记」子节，4 个文件引用

## 最终状态

```
05-applications/
├── applications-business/
│   └── ai-driven-community-operation/
│       ├── README.md              # 1,212字（含模板+经验）
│       ├── 圈层活动案例集.md       # 5,662字（13案例合集）
│       └── RAG配置说明.md          # 547字
└── applications-quant/
    └── 成长因子的选股策略.md       # 28KB（保留）
```

22 个文件 → 4 个文件，内容零损失。

## 关键经验

1. **分类索引表是合集的灵魂**：13 个案例如果只是简单拼接，找东西反而更难。顶部加分类+亮点表后，5 秒内可定位。
2. **合并前先读内容**：13 个案例结构高度一致（基本信息/活动内容/效果总结/经验沉淀），适合合并；如果结构差异大则不宜。
3. **README 作为唯一入口**：目录瘦身后的 README 承担了「文件结构说明+模板+经验总结」三重角色。
4. **index.md 同步更新不能忘**：删除目录后若 index.md 不更新，跑 wiki_lint 会报死引用。
