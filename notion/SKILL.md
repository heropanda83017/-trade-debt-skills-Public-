---
name: notion
description: Notion workspace 读写 + 报告分发。支持搜索页面、获取内容、写入段落、自动生成美化日报。触发词：「查 Notion」「看看 Notion」「Notion 里」「写入 Notion」「同步 Notion」「Notion 报告中心」。
version: "2.0"
author: hermes-agent
changelog: |
  v2.2 — 新增「写入后不等用户反馈直接完成」的工作流说明；精简示例代码中的冗余注释
  v2.1 — 新增报告追加模式（只追加不覆盖）的完整文档；新增趋势总览维护策略；新增行为禁止清单（避免误删历史）
  v2.0 — 新增报告分发模式：Hermes 报告中心页面结构、美化格式写入、分批 block 写入、已知坑合集。页面权限/UUID问题文档化。
  v1.0 — 基础搜索/读取/写入功能。
---

# Notion 操作技能

对接用户 Notion workspace，通过 Notion API 读写页面内容。支持基础操作和高质量报告分发。

## 工具

本 skill 提供三个 Python 函数，通过 `execute_code` 调用：

### 1. 搜索页面

```python
notion_search(query: str, page_size: int = 10) -> list[dict]
```

- 根据关键词搜索 workspace 中的页面
- 返回：页面ID、标题、类型、最后更新时间
- 示例：`notion_search("理想之地 营销")`
- **注意**：Notion API 搜索对无标题页面返回空字符串，需配合其他属性判断

### 2. 获取页面内容

```python
notion_get_page(page_id: str) -> dict
```

- 获取指定页面的完整内容和属性
- 返回：标题、创建时间、更新时间、所有区块内容

### 3. 写入页面段落

```python
notion_append_block(page_id: str, content: str, block_type: str = "paragraph") -> bool
```

- 向指定页面追加文本段落
- block_type 可选：`paragraph` / `heading_1` / `heading_2` / `bulleted_list_item`

## 使用前提

- Python 包 `notion-client` 已安装
- `NOTION_API_KEY` 已写入 `~/.hermes/.env`
- Key 已在上一轮验证有效
- **页面必须与集成（Hermes助手）分享**：页面右上角「···」→「添加连接」→ 搜索集成名称

## 报告分发模式

### 推荐页面结构（Hermes 报告中心）

```
📊 Hermes 报告中心（侧边栏顶层页面—用户手动创建）
  ├── 📊 小红书舆情日报      ← 每日写入
  ├── 🏗️ 恒江雅筑维稳简报   ← 每两日写入
  ├── 🔍 竞品动态周报        ← 每周写入
  └── 📈 销售数据日报        ← 工作日写入
```

**注意**：Notion 内部集成**不能创建 workspace 级别的顶层页面**。用户必须在侧边栏手动创建后授权集成。

### 美观格式写入（推荐用于报告）

使用丰富的 block 类型构建可读性高的报告页面：

```python
from notion_client import Client

client = Client(auth=NOTION_KEY)
page_id = "完整36位UUID"

# 0. 清空现有内容
existing = client.blocks.children.list(block_id=page_id)
for b in existing.get("results", []):
    client.blocks.delete(block_id=b["id"])

# 1. 构建 blocks 列表
blocks = []

# 标题
blocks.append({
    "object": "block", "type": "heading_1",
    "heading_1": {"rich_text": [{"type": "text", "text": {"content": "📊 日报标题"}}]
})

# 正文（带样式）
blocks.append({
    "object": "block", "type": "paragraph",
    "paragraph": {
        "rich_text": [
            {"type": "text", "text": {"content": "加粗", "annotations": {"bold": True}}},
            {"type": "text", "text": {"content": " 普通 "}},
            {"type": "text", "text": {"content": "红色", "annotations": {"color": "red"}}},
        ]
    }
})

# 分割线
blocks.append({"object": "block", "type": "divider", "divider": {}})

# 列表项
blocks.append({
    "object": "block", "type": "bulleted_list_item",
    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "列表内容"}}]}
})

# 高亮块（callout）— 用于关键发现/告警
blocks.append({
    "object": "block", "type": "callout",
    "callout": {
        "rich_text": [{"type": "text", "text": {"content": "⚠️ 重要发现", "annotations": {"bold": True}}}],
        "icon": {"emoji": "⚠️"},
        "color": "yellow_background"  # 或 red_background / green_background / blue_background
    }
})

# 二级标题
blocks.append({
    "object": "block", "type": "heading_2",
    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "二、分析结果"}}]
})

# 2. 分批写入（每批不超过10个）
for i in range(0, len(blocks), 10):
    client.blocks.children.append(block_id=page_id, children=blocks[i:i+10])
```

### block type 对照表

| Notion block | Python dict type | 适用场景 |
|-------------|-----------------|---------|
| Heading 1 | `heading_1` | 文档标题 |
| Heading 2 | `heading_2` | 章节标题 |
| Paragraph | `paragraph` | 正文 |
| Bulleted list | `bulleted_list_item` | 列表项 |
| Divider | `divider` | 分割线 |
| Callout | `callout` | 高亮关键信息 |
| To-do | `to_do` | 待办清单 |

### annotations 可选项

```python
annotations = {
    "bold": True,        # 加粗
    "italic": True,      # 斜体
    "strikethrough": True,  # 删除线
    "underline": True,   # 下划线
    "code": True,        # 代码样式
    "color": "red"       # 颜色: default/gray/brown/orange/yellow/green/blue/purple/pink/red
}
```

## 报告追加模式（只追加不覆盖）

> 用户明确要求：所有定期报告必须用追加模式，不删历史，可回溯趋势。

### Hermes 报告中心页面结构

报告中心固定4个子页面，位于用户侧边栏顶层：

```
📊 Hermes 报告中心（用户手动创建并授权，page_id: 369d2d6a-b18a-8062-9568-c2e2f39055ec）
  ├── 📊 小红书舆情日报      ← 每日写入
  ├── 🏗️ 恒江雅筑维稳简报   ← 每两日写入
  ├── 🔍 竞品动态周报        ← 每周写入
  └── 📈 销售数据日报        ← 工作日写入
```

**创建注意**：Notion 内部集成不能创建 workspace 级顶层页面。用户手动创建空白页面后，右上角「···」→「添加连接」→搜索「Hermes助手」授权。

### 适用报告类型

| 报告 | 频率 | Notion 页面 |
|------|------|------------|
| 小红书舆情日报 | 每日 | `📊 小红书舆情日报` |
| 恒江雅筑维稳简报 | 每两日 | `🏗️ 恒江雅筑维稳简报` |
| 竞品动态周报 | 每周 | `🔍 竞品动态周报` |
| 销售数据日报 | 工作日 | `📈 销售数据日报` |

### 推荐页面结构

```
┌─ 顶部：最新摘要 / 逐日趋势行（一目了然看变化）
├─ 📜 历史日志（从新到旧，每次追加在末尾）
│   ├─ 2026-05-23 ← 最新
│   ├─ 2026-05-22
│   └─ 2026-05-17
└─ 页脚：生成标识
```

### 追加写入（非覆盖）

```python
# ✅ 追加模式——只留新、不删旧
# 读取已有 blocks 数量
existing = client.blocks.children.list(block_id=page_id)
n_existing = len(existing.get("results", []))

# 构建新 blocks
new_blocks = [
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "heading_3",
     "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📅 2026-05-23"}}]}},
    # ... 更多正文blocks
]

# 直接 append（自动排在末尾）
for i in range(0, len(new_blocks), 10):
    client.blocks.children.append(block_id=page_id, children=new_blocks[i:i+10])
```

### ❌ 禁止的覆盖写法

```python
# ❌ 不要这样做——会清空历史
existing = client.blocks.children.list(block_id=page_id)
for b in existing.get("results", []):
    client.blocks.delete(block_id=b["id"])  # 删掉所有历史
```

### 趋势总览的维护

如果页面顶部有逐日趋势行（如销售日报的每日对比行），追加新日数据时需同时**更新顶部的趋势行**。操作步骤：

1. 读取页面前 10-15 个 blocks
2. 识别趋势行区域（通常为 `divider` 之间的段落块）
3. 重新构建趋势区 blocks（清空后重写，因为需要插入新行到中间位置）
4. 下方的历史日志 blocks 不动（追加模式）
5. 趋势区要用覆盖模式，但历史区用追加模式——两者不冲突

```python
# 销售日报趋势行示例（顶部）
# 日期      来访          认购            网签            回款
# 05-22    26组        0套/0万       1套/346万       43万
# 05-17    45组        2套/894万       —              —
# → 追加 05-23 的数据行到趋势区，同时不清历史日志

# 实现方式：清空页面→重建趋势区（含新行）→追加历史日志（含旧的全部+新的）
# 但这样会丢失历史日志的趋势对比价值
# 更优方案：不动趋势区（手工维护），只在历史日志区追加
```

1. 读取页面前 10-15 个 blocks
2. 识别趋势行区域（通常为 `divider` 之间的段落）
3. 在趋势区域末尾插入新行
4. 不要动下方历史日志 blocks

```python
# 趋势行示例（销售日报）
# 05-22    26组      0套/0万      1套/346万      43万
# 05-17    45组      2套/894万      —             —
# → 追加 05-23 的数据行到趋势区末尾
```

### 页面初始化

首次搭建报告页面时，用覆盖模式写入骨架（趋势区 + 第一条历史日志），后续全部用追加模式：

```python
# 第一次：覆盖写入骨架
blocks = [
    h1("报告标题"),
    p([t("趋势行...")]),
    divider(),
    h2("📜 历史日志"),
    h3("📅 2026-05-22"),
    p([...]),  # 第一条历史数据
    divider(),
    p([t("生成标识", italic=True, color="gray")]),
]
# 用 append 写入（因为是空页面，append 就是第一次写入）

# 后续：只用追加模式加新日志
```

## 已知坑

| 问题 | 原因 | 解法 |
|------|------|------|
| `page_id` 不够36位 | 显示截断 | 从 search 结果取完整 UUID |
| `ObjectNotFound` | 未分享页面 | 用户手动在页面授权集成 |
| 不能创建顶层页面 | 内部集成限制 | 用户手动创建后授权 |
| 写入超时 | Notion API 慢 | timeout=120s, 每批≤10 blocks |
| 搜索不到新页面 | 索引延迟 | 等数秒或用其他关键词 |

## 错误处理

- 返回 `{"error": "描述"}` 时说明权限问题或网络问题
- 页面不存在返回404
- Key 无效返回401

## 关联技能

- `xhs-sentiment-monitoring` — 舆情日报的 Notion 分发对接方式
- `school-district-crisis-response` — 危机报告的 Notion 分发（含 `references/notion-report-delivery.md`）

## 调用示例

**搜索：**
```python
notion_search("理想之地 学区")
```

**读取：**
```python
notion_get_page("完整36位page_id")
```

**写入美观报告：**
```python
blocks = [
    {"object": "block", "type": "heading_1",
     "heading_1": {"rich_text": [{"type": "text", "text": {"content": "📊 舆情日报"}}]}},
    {"object": "block", "type": "divider", "divider": {}},
    {"object": "block", "type": "paragraph",
     "paragraph": {"rich_text": [{"type": "text", "text": {"content": "报告正文"}}]}},
]
for i in range(0, len(blocks), 10):
    client.blocks.children.append(block_id=page_id, children=blocks[i:i+10])
```
