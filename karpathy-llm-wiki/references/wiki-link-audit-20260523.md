# Wiki 链接网络审计实录（2026-05-23）

## 背景

对理想之地 wiki（约35个核心实体页 + 7个概念页）进行系统性链接网络审计，
识别孤立页面、补充双向链接、重构 index.md 为销售驱动仪表盘。

## 审计流程

### 1. 全量扫描

遍历所有 .md 文件，对每个文件统计：
- 出链数 = `re.findall(r'\[\[([^\]]+)\]\]', content)`
- 入链数 = 反向索引中指向本页的页面数量

```python
page_links = {}  # page -> set(linked pages)
for root, dirs, files in os.walk(wiki_dir):
    for f in files:
        if not f.endswith('.md'): continue
        rel = os.path.relpath(os.path.join(root, f), wiki_dir)
        with open(...) as fh:
            links = re.findall(r'\[\[([^\]]+)\]\]', fh.read())
        page_links[rel] = set(link.split('|')[0].split('#')[0].strip().lower() for link in links)

reverse = {}
for page, linked in page_links.items():
    for target in linked:
        if target not in reverse: reverse[target] = []
        reverse[target].append(page)
```

### 2. 问题分类

| 状态 | 出链 | 入链 | 处理方式 |
|------|------|------|---------|
| 🔴 孤立 | =0 | =0 | 删除或加链接 |
| 🟡 单向 | >0 | =0 | 从相关页面链入 |
| 🟢 双向 | >0 | >0 | 健康 |

### 3. 修复模式

**缺失入链的修复：**

| 孤立页 | 在哪个页面加链接 | 加什么 |
|--------|----------------|--------|
| daily-sales-data.md | sales-funnel.md | `[[daily-sales-data]]` |
| daily-sales-data.md | ideal-land-project.md | `[[daily-sales-data]]` |
| project-milestone-timeline.md | project-engineering.md | `[[project-milestone-timeline]]` |
| project-talent-policy.md | policy-context.md | `[[project-talent-policy]]` |

**缺失出链的修复：**

| 页面 | 补充的出链 |
|------|-----------|
| daily-sales-data.md | ideal-land-project, sales-funnel, visitor-analysis, may-marketing-plan |
| project-milestone-timeline.md | ideal-land-project, project-engineering, project-design-overview |
| project-talent-policy.md | policy-context, ideal-land-project, sales-funnel |

### 4. 散落页面处理

| 页面 | 大小 | 处理 |
|------|------|------|
| raw/policies/两篇 | <500字 | 删除，改为直链源文件路径 |
| entities/weekly-report | 957字 | 移入 _archive/ |
| events/会议记录 | 4158字 | 保留，在 circle-activities.md 加链接 |
| queries/开学季方案 | 1392字 | 保留，在 yichuxueyuan.md 加链接 |
| raw/articles/营销数据 | 2659字 | 保留，在 sales-funnel/visitor-analysis 加链接 |

### 5. index.md 重构

从扁平列表改为销售驱动仪表盘结构：
- 🎯 核心目标（销售数据/转化漏斗/来访画像）
- 📡 四维驱动（政策/宣传/活动/管理）
- 📊 Notion 报告中心入口
- 📁 资料归档