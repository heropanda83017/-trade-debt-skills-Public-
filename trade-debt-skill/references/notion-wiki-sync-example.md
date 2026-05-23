# Notion→Wiki 同步实例（2026-05-07）

## 场景
用户要求从 Notion 读取"拓展金瀚卓越业务"系列页面，同步到本地 wiki。

## 执行步骤

### Step 1: 搜索
```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "金瀚卓越"}' -o /tmp/notion_search.json
```

搜索结果：100条（含60+金瀚相关页面 + 理想之地等无关页面）

### Step 2: 筛选并读取最新页面
读取编号最高的9个页面（105-115），通过 Python 批量拉取：

```python
import subprocess, json, os
api_key = os.environ.get('NOTION_API_KEY')
headers = [
    "Authorization: Bearer " + api_key,
    "Notion-Version: 2025-09-03",
    "Content-Type: application/json"
]
pages = {
    "115_华源证券": "359d2d6a-b18a-80a9-ad53-d28303a1d119",
    # ...
}
for name, pid in pages.items():
    url = f"https://api.notion.com/v1/blocks/{pid}/children?page_size=50"
    result = subprocess.run(["curl", "-s", url, "-H", headers[0], ...], capture_output=True)
    with open(f"/tmp/notion_{name}.json", 'w') as f:
        json.dump(json.loads(result.stdout), f, ensure_ascii=False)
```

### Step 3: 提取文本内容
```python
def extract_text_from_block(block):
    texts = []
    block_type = block.get('type', '')
    content = block.get(block_type, {})
    for field in ['rich_text', 'text']:
        if field in content:
            for rt in content[field]:
                if isinstance(rt, dict) and 'plain_text' in rt:
                    texts.append(rt['plain_text'])
    if 'children' in content:
        for child in content['children']:
            texts.extend(extract_text_from_block(child))
    return texts
```

### Step 4: 增量对比发现
| 发现 | 重要度 | 对应更新 |
|------|--------|---------|
| 调解书未履行（2月底分期20万×3=0） | 🔴 重大 | entities/shanghai-liye.md + 催收日志 |
| 四川路桥保全事件 | 🟡 补充 | 同上 |
| 山鹰国际已起诉并立案 | 🟡 补充 | 同上 |
| 煤交所10月挂牌重组 | 🟢 机会 | 同上 |
| 安徽国贸债权修正(3000万→4000万) | 🟢 修正 | 同上 |
| 宝钺2025年营收1000万 | 🟡 补充 | entities/hunan-baoye.md |
| 宝钺BP首年5000万/正循环1亿 | 🟡 补充 | 同上 |

### Step 5: 并行更新
采用 delegate_task 分两轮更新：
- 第一轮：entities/shanghai-liye.md + entities/hunan-baoye.md + 01-债务人档案/上海理业.md
- 第二轮：entities/debt-overview.md（追加动态）+ 04-催收记录/追加记录

### Step 6: 保存原始数据
写入 `09-参考素材/Notion金瀚业务原始提取20260507.md` 作为本地缓存。

### 耗时统计
| 阶段 | 耗时 |
|------|------|
| API读取（9页并行） | ~11s |
| 内容提取+分析 | ~0.2s |
| delegate_task并行更新（2轮） | ~49s |
| 总计 | ~60s |

## 注意事项
- Notion 页面可能超过50 blocks，需检查 `has_more` 字段
- 搜索结果中会混入无关页面（如"理想之地"），需按命名前缀"拓展金瀚卓越业务"筛选
- 编号高的页面（如115）是最新的，编号低的是历史记录
- 保存原始数据到09-参考素材是必要的，避免重复调用API
