# 源文件→Wiki 知识管线

从 `源文件/` 目录（PDF/docx/xlsx/pptx）全量提取关键信息，对比现有 wiki 后增量更新知识库。

## 适用场景

- 830+ 文件/6.5GB 的源文件目录，需要从中提取结构化学识到 wiki
- 文件类型混合（PDF + docx + xlsx + pptx + png + dwg）
- 目标：不重复 wiki 已有内容，只补充新增信息
- 一次性处理多个目录（工程设计/成本/配套/营销/运营/汇报等）

## 通用工作流

### Step 0：全景扫描

了解目录结构和内容类型，决定处理策略：

```python
from pathlib import Path
base = Path("E:/Landofdream/源文件")

for d in sorted(base.iterdir()):
    files = list(d.rglob('*'))
    pdfs = [f for f in files if f.suffix=='.pdf']
    docxs = [f for f in files if f.suffix in ['.docx','.doc']]
    xlsx = [f for f in files if f.suffix in ['.xlsx','.xls']]
    total_mb = sum(f.stat().st_size for f in files) / 1024 / 1024
    print(f"{d.name}/ — {len(files)}个/{total_mb:.0f}MB, pdf={len(pdfs)}, docx={len(docxs)}, xlsx={len(xlsx)}")
```

### Step 1：统一文本提取

单一函数覆盖所有格式：

```python
import fitz
from docx import Document
import openpyxl

def extract_text(file_path):
    ext = file_path.suffix.lower()
    text = ""
    try:
        if ext == '.pdf':
            doc = fitz.open(str(file_path))
            # 大PDF(MB级)：只取每页前500字符
            text = "\n".join([p.get_text()[:500] for p in doc])
            doc.close()
        elif ext in ['.docx', '.doc']:
            doc = Document(str(file_path))
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext == '.xlsx':
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    r = " | ".join([str(c)[:60] for c in row if c])
                    if r.strip(): text += r + "\n"
            wb.close()
    except:
        pass
    return text
```

### Step 2：对比现有 wiki

```python
existing = wiki_path.read_text(encoding='utf-8')
# 判断新内容的标准：
# 1. 文件标题/关键词不在 existing 中出现
# 2. 核心数据（数字/金额/比率）不在 existing 中
# 3. 新事件/新决策/新进展不在 existing 中
```

### Step 3：增量插入 wiki

标准插入模式——在 `## 参考` 之前追加内容：

```python
new_section = "\n## 新增内容\n\n..."
if "## 参考" in existing:
    existing = existing.replace("## 参考", new_section + "\n## 参考")
else:
    existing += "\n" + new_section

# 更新日期
import re
existing = re.sub(r'updated: [\d-]+', 'updated: 2026-05-23', existing)
wiki_path.write_text(encoding='utf-8', data=existing)
```

## 多目录批处理策略

### 优先级排序

| 优先级 | 目录类型 | 典型体量 | 策略 |
|--------|---------|---------|------|
| P0 | 专项目录（设计/工程/成本/学校） | <200MB | 全量提取+更新对应实体wiki页 |
| P1 | 小目录（财务/拿地/市政） | <50MB | 全量提取，合并更新到已有wiki页 |
| P2 | 运营目录（商业/物业/大健康/智慧等9板块） | >1.5GB | 按子目录分别更新对应wiki页 |
| P3 | 大目录（营销/汇报） | >500MB | 只提取关键docx，跳过大量活动方案PPT |

### 并行限制

- `delegate_task` 最多 3 个并发子任务
- 大 PDF（>50MB）子任务容易超时（202 秒），建议直接在当前会话逐个处理
- 小文件目录可以合并到同一个子任务中处理

### 文件大小阈值判断

- <1MB → 全量提取文本
- 1-50MB → 每页限制 500 字符
- >50MB → 跳过（纯图片/渲染PDF），仅记录文件名索引

## 实战案例（2026-05-23 全源文件深度学习）

8 个目录 × 830 个文件 × 6.5GB → 更新 13 个 wiki 页：

| 批次 | 目录 | 处理方式 | 更新wiki页数 |
|------|------|---------|-------------|
| Batch 1 | 02工程/ + 03成本/ + 04学校/ | 逐个处理，大PDF每页500字 | 3页（工程/成本/学校） |
| Batch 2 | 07财务/ + 10拿地/ + 08运营/ | 小目录全量+运营按子目录 | 8页（财务/拿地/商业/物业/大健康/智慧/青年/招引） |
| Batch 3 | 06营销/ + 09汇报/ | 只提取关键docx，跳过活动方案PPT | 4页（营销/圈层/政府背书/新模式/定位） |

### 关键结论

1. **pymupdf 效率极高**：196MB的PDF打开只需0.2秒，全量扫描9个PDF（600页）1.2秒完成
2. **docx 是最佳信息来源**：会议记录/方案汇报/研究报告含结构化文本，提取质量高
3. **PPT/PNG/DWG**：无法提取文本，仅记录文件名
4. **xlsx 提取有限**：含大量公式和数字，纯文本提取后语义稀疏，需要人工解读
5. **wiki 增量更新**：对比现有内容后只补充新信息，不改动已有内容

## 已知限制

- 大PPT（>50MB）含大量图片+少量文本，提取价值低
- 扫描件PDF无文字层 → pymupdf 返回空，需OCR
- xlsx 多sheet 只读 active sheet
- `delegate_task` 超时阈值为 202 秒，大文件不要走子任务
