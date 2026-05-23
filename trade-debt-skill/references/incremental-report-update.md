# 增量报告更新模式

> **来源：** 2026-05-20 宝钺案 v3→v4 报告更新实操总结
> **配套章节：** trade-debt-skill 9.6b

---

## 适用判断

当同时满足以下条件时，使用增量更新模式：
- ✅ 已有目标报告（`_v3.md/.docx`）存在
- ✅ 新收到信息源（会议纪要/电话会/尽调补充）
- ✅ 新信息属于"补充到现有报告"而非"重写框架"
- ✅ 目的不是向集团/审计的正式汇报（那是 T-REP 模式）

不满足时 → 使用 9.1 节从零编译模式。

---

## 标准工作流

### Step 1：读取源文件（会议纪要/新增信息）

```python
# .docx 解析（会议纪要/报告均为 docx）
import zipfile, xml.etree.ElementTree as ET

def extract_docx_text(path):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(path) as z:
        tree = ET.parse(z.open('word/document.xml'))
    root = tree.getroot()
    body = root.find('.//w:body', ns)
    lines = []
    for para in body.findall('.//w:p', ns):
        texts = [t.text for t in para.findall('.//w:t', ns) if t.text]
        if texts:
            lines.append(''.join(texts))
    return '\n'.join(lines)
```

### Step 2：读取目标报告

```python
# .docx 目标报告 → 同上 extract_docx_text()
# .md 目标报告 → open().read()
```

### Step 3：差异分析（核心）

建立差异分析表，决定每个章节的处理方式：

| 章节 | 目标报告(v3)内容 | 源文件新增内容 | 处理方式 | 说明 |
|------|----------------|--------------|---------|------|
| 企业沿革 | #120数据 | 会议纪要补充企业沿革 | **修正** | 以会议纪要时间线为准 |
| 良品率 | 引用审计40% | 会议纪要确认当前60% | **修正** | 标注数据来源差异 |
| 债务情况 | 笼统列示 | 明确光大5月到期+轩达代偿意向 | **修正** | 更新债务时间线 |
| 供应商债务 | 未提及 | "1-2-3-3"五年分期方案 | **新增** | 补充至债务处理章节 |
| 资金需求 | 未细化 | 偿债1000万+运营2000-3000万+储备 | **新增** | 新增资金需求章节 |
| 生产工艺 | 无 | 详细工艺流程+质量控制体系 | **新增** | 补充行业章节 |
| 行业背景 | 简略 | 详细市场驱动因素+竞争格局 | **扩充** | 增强行业章节 |
| *其他章节* | *—* | *无新增* | **保留** | 直接沿用v3内容 |

**三种处理方式：**
- **新增**：源文件有，目标报告无 → 在合适位置插入新章节
- **修正**：源文件有，且与目标报告矛盾 → 替换目标报告对应内容，标注来源
- **保留**：目标报告内容未被源文件更新 → 原样保留

### Step 4：写入新版本 Markdown

格式：`[报告名]_[日期]_v[N].md`

```markdown
*报告版本：v4.0*
*更新内容：整合0520华源现场会议纪要（逐项列举）*
*下次更新触发条件：预重整方案正式提交 / 产业投资人确定 / 金瀚国资审批通过*
```

### Step 5：Markdown → .docx

使用 execute_code（见 9.6b 执行原则），见下方代码模板。

---

## 差异分析表示例（本次宝钺 v3→v4）

| # | 更新项 | v3内容 | v4内容 | 来源 | 处理 |
|---|--------|--------|--------|------|------|
| 1 | 光大银行到期 | 笼统列为风险 | 明确5月到期+轩达可能代偿 | 0520纪要 | 修正 |
| 2 | 良品率 | 审计40% | 当前60%（会议确认） | 0520纪要 | 修正 |
| 3 | 供应商债务方案 | 未提及 | "1-2-3-3"五年分期 | 0520纪要 | 新增 |
| 4 | 建设银行态度 | 未提及 | 同意展期+利息改年/半年付 | 0520纪要 | 新增 |
| 5 | 资金分配 | 未细化 | 偿债1000万+运营2000-3000万+储备 | 0520纪要 | 新增 |
| 6 | 生产工艺 | 无 | 详细工艺流程+质量控制体系 | 0520纪要 | 新增 |
| 7 | 各方共识 | 无 | 5条基本共识（联合投资等） | 0520纪要 | 新增 |
| 8 | 股东博弈 | 无 | 原股东 vs 产业方控制权分歧 | 0520纪要 | 新增 |

---

## Markdown → DOCX 代码模板

```python
import subprocess, sys, re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

subprocess.run([sys.executable, '-m', 'pip', 'install', 'python-docx', '-q'],
               capture_output=True)

def md_to_docx(md_path, docx_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    doc = Document()
    lines = content.split('\n')
    in_table = False
    table_headers = []
    table_lines = []

    for line in lines:
        if line.strip() == '---':
            continue
        if line.startswith('# ') and not line.startswith('## '):
            h = doc.add_heading(line[2:], 0)
            for r in h.runs:
                r.font.name = 'Calibri'
                r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        elif line.startswith('## '):
            h = doc.add_heading(line[3:], 1)
            for r in h.runs:
                r.font.name = 'Calibri'
                r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        elif line.startswith('### '):
            h = doc.add_heading(line[4:], 2)
            for r in h.runs:
                r.font.name = 'Calibri'
                r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        elif line.startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c.strip()) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_headers = cells
            else:
                table_lines.append(cells)
        else:
            if in_table:
                in_table = False
                tbl = doc.add_table(rows=1, cols=len(table_headers))
                tbl.style = 'Table Grid'
                hdr = tbl.rows[0]
                for i, h_text in enumerate(table_headers):
                    hdr.cells[i].text = h_text
                    hdr.cells[i].paragraphs[0].runs[0].bold = True
                for row_data in table_lines:
                    row = tbl.add_row()
                    for i, c in enumerate(row_data):
                        row.cells[i].text = c
                table_lines = []
                table_headers = []
            if line.strip():
                p = doc.add_paragraph()
                parts = re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', line)
                for part in parts:
                    run = p.add_run(part)
                    run.font.name = 'Calibri'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                    if part.startswith('**') and part.endswith('**'):
                        run.bold = True

    doc.save(docx_path)
    print(f'OK: {docx_path}')

md_to_docx(
    '/mnt/e/TradeDebt/源文件/09-参考素材/湖南宝钺/湖南宝钺综合研判报告_20260520_v4.md',
    '/mnt/e/TradeDebt/源文件/09-参考素材/湖南宝钺/湖南宝钺综合研判报告_20260520_v4.docx'
)
```

---

## 版本号管理

| 场景 | 版本规则 | 示例 |
|------|---------|------|
| 首次发布 | v1.0 | _v1.0.docx |
| 小幅修正（错别字/格式） | v1.1 | _v1.1.docx |
| 内容补充（新增章节/数据） | v1.2 | _v1.2.docx |
| 重大修订（框架调整） | v2.0 | _v2.0.docx |
| 整合多源信息 | v[N].0 | _v4.0.docx |

本次更新：v3.0 → v4.0（多源整合，框架未变，内容大幅补充）。
