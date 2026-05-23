# Notion → Wiki 每周消化示例（2026-05-23 执行实录）

## 背景

周六例行 Notion 工作记录消化。胡盼的 Notion 中本周（5/16-5/22）有约 5 则工作记录，以无标题空页面形式存在。

## 执行步骤

### 1. 搜索 Notion 本周页面

```python
from notion_client import Client
client = Client(auth=NOTION_API_KEY)

# 多关键词搜索覆盖
searches = ['工作记录', '每周工作', '日报', '周报', '2026年5月', '2026-05']
for q in searches:
    res = client.search(query=q, page_size=5)
    # 注意：页面 title 可能为空，需通过 last_edited_time 筛选
```

**发现：** 页面标题全为空，需通过 `last_edited_time` 判断时效性，通过 `blocks.children.list()` 读取前几段内容判断主题。

**Notion 空标题页面的确认模式：** 胡盼的工作记录页面 title 属性始终为空字符串。这是 Notion 数据库视图的行为，不会影响页面内容搜索。搜索时用 `"工作记录"` 等关键词能找到全部页面，无需依赖标题。读取时用 `blocks.children.list(block_id=page_id)` 获取内容块即可。

### 2. 阅读 Notion 页面内容

```python
blocks = client.blocks.children.list(block_id=page_id)
for b in blocks.get('results', [])[:5]:
    btype = b.get('type', '')
    content = b.get(btype, {})
    if 'rich_text' in content:
        texts = [t.get('text', {}).get('content', '') for t in content['rich_text']]
        print(''.join(texts)[:100])
```

### 3. 筛选与分类

| Notion 内容 | 分类 | 目标 wiki 页 |
|-------------|------|-------------|
| 教育局沟通：一初学苑确认但划片需明年；恒江雅筑跨区问题；转校操作 | 学区进展 | `yichuxueyuan.md` |
| 学校装修财评（4周周期）；一装二装设计碰头会；校园文化/基仪站 | 工程进展 | `project-engineering.md` |
| 华源证券合作：财富私享沙龙每月1场；专属基金产品 | 圈层活动 | `circle-activities.md` |
| 郭敏谈话；薪酬考核；购房协调 | 内部管理 | ❌ 不沉淀 |

**跨项目风险（新增类型）：** 当 Notion 中出现同集团其他项目（如恒江雅筑）的学区/维稳信息时，需同步记录到 `yichuxueyuan.md` 的"学校最近工作动态"章节末尾，以"⚠️"标注。这类内容同时归档至源文件目录（`04周边配套/学校/提请区教育局学区资源/`）。

### 4. wiki 页面更新

使用 Python `open()` 读写（绕过 read_file 的路径解析问题）：

```python
with open(r'E:\Landofdream\wiki\entities\yichuxueyuan.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 "关联页面" 前插入新章节
new_section = '''### xxx 标题

**来源：** Notion工作记录（2026-05-22）
...内容...
'''
content = content.replace('\n## 关联页面', new_section + '\n\n## 关联页面')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**注意：** 同时更新 frontmatter 中的 `updated:` 日期。

### 5. wiki_lint 手动体检

由于 Windows 下 `search_files` 需要 ripgrep，`read_file` 路径解析有问题，改用 Python 手动检查：

```python
import os, re
from datetime import datetime, timedelta

issues = []
# 遍历所有 .md 文件
for root, dirs, files in os.walk(r'E:\\Landofdream\\wiki'):
    for f in files:
        if not f.endswith('.md'):
            continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        # 检查 frontmatter
        if not content.startswith('---'):
            issues.append(f'{f}: Missing frontmatter')
        
        # 检查 wiki 链接
        links = re.findall(r'\\[\\[([^\\]]+)\\]\\]', content)
        for link in links:
            page = link.split('|')[0].strip()
            # 检查目标文件是否存在...
        
        # 检查常见格式错误
        if '\\\\|' in content:
            # [[page\\\\|text]] → [[page|text]]
            # 精确修复：匹配 [[page\\|display]]（一个反斜杠+管道符）
            content = re.sub(r'\\[\\[([^\\]|]+)\\\\\\|', r'[[\\1|', content)
```

**注意：** `[[page\\|display]]` 中的 `\\` 在文件里是**一个**反斜杠字符，Python 正则中需写 `\\\\` 来匹配。修复后重新运行链接完整性检查确认。
```

### 6. 报告输出

向用户总结：
- ✅ Step 1 完成：找到了 N 条工作记录
- ✅ Step 2 完成：更新了 X 个 wiki 页面
- ✅ Step 3 完成：修复 Y 处问题，wiki 健康度 GOOD

## 本次执行成果

- Notion 本周记录：5 条（学校学区/工程/华源证券/人事/杂项）
- 沉淀进 wiki：3 页（yichuxueyuan / project-engineering / circle-activities）
- lint 修复：12 处 `[[page\\|display]]` → `[[page|display]]` 格式错误
- wiki 总页数：48，健康度 GOOD
