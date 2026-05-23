# Python + 中文内容技术陷阱手册

> 来源：2026-05-20 宝钺 Word 报告生成实战教训
> 适用：生成 python-docx 报告、Excel 数据处理等含中文内容的 Python 脚本

---

## 陷阱 1：中文引号 `"..."` 导致 Python SyntaxError

### 问题现象

Python 解析时报 `SyntaxError: invalid syntax`，指向某行中间位置。

```python
# 这行会报错：
add_green_ok(doc, "关键判断："民营背景在两机领域难以立足"，宝钺必须引入央国企投资人")
#                      ^ 第二、三个 " 被误认为字符串边界

# 这行不会报错（单引号包裹）：
add_green_ok(doc, '关键判断："民营背景在两机领域难以立足"，宝钺必须引入央国企投资人')
```

### 根因

Unicode U+201C `"` 和 U+201D `"`（中文/弯引号）在视觉上与 ASCII 双引号 `"`（U+0022）高度相似。Python 解析器在遇到第 2 个 `"` 时认为字符串结束了，后续字符变成语法错误。

### 诊断三步法

```python
# Step 1: 运行 ast.parse 定位问题行
import ast
with open('script.py','r',encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
except SyntaxError as e:
    print(f"Line {e.lineno}: {e.msg}")

# Step 2: 确认是哪个字符
with open('script.py','rb') as f:
    lines = f.read().split(b'\n')
line = lines[error_lineno - 1]
for i, b in enumerate(line):
    if b == 0x22:  # ASCII 双引号
        print(f"  ASCII quote at byte {i}")
    # 检测 U+201C / U+201D
    if line[i:i+3] == b'\xe2\x80\x9c':
        print(f"  U+201C (") at byte {i}")
    if line[i:i+3] == b'\xe2\x80\x9d':
        print(f"  U+201D (") at byte {i}")

# Step 3: 全局修复
with open('script.py','r',encoding='utf-8') as f:
    content = f.read()
content = content.replace('\u201c','\u300e').replace('\u201d','\u300f')  # " → 「」
with open('script.py','w',encoding='utf-8') as f:
    f.write(content)
ast.parse(content)  # 验证修复
```

### 预防规则（两条）

1. **写脚本时**：含中文内容的 Python 脚本，**所有字符串用单引号 `'...'` 包裹**
2. **写完后**：立即运行 `ast.parse()` 验证语法，再执行脚本

---

## 陷阱 2：python-docx 表格 cell.text = '' 后 run.font 丢失

### 问题现象

设置单元格背景色后，单元格字体变成默认的 Calibri，无法设置中文字体。

### 根因

`cell.text = 'value'` 会重置单元格所有格式。正确做法是操作已有 paragraph 的 run。

### 正确写法

```python
from docx.oxml.ns import qn

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_text(cell, text, bold=False, size=9, font='SimSun', color_rgb=None):
    """向单元格写入文本（保留原有格式）"""
    p = cell.paragraphs[0]
    p.clear()  # 清空但保留基本 paragraph 格式
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font
    run._r.rPr.rFonts.set(qn('w:eastAsia'), font)  # 中文字体
    if color_rgb:
        run.font.color.rgb = color_rgb
    return p
```

---

## 陷阱 3：python-docx 中文字体在不同平台显示异常

### 根因

Windows 的 Word 对中文字体的 `rFonts`（西文字体）和 `eastAsia`（东亚字体）分开设置，只设置 `r.font.name = 'SimSun'` 不足以让 Word 正确渲染中文。

### 正确写法

```python
from docx.oxml.ns import qn

run.font.name = 'SimHei'
run._r.rPr.rFonts.set(qn('w:eastAsia'), 'SimHei')
```

必须在设置 `font.name` 后，同时在 run 的 XML 中设置 `w:eastAsia` 字体，才能在 Word 中正确显示。

---

## 陷阱 4：长脚本中 patch 多次导致文件状态混乱

### 问题现象

对一个 700+ 行的脚本文件执行多次 `patch` 操作后，后续 patch 报错 `"old_string not found"`，因为中间某次 patch 已经改变了文件的相对内容，导致后续 old_string 无法匹配。

### 根因

`patch` 工具基于精确字符串匹配，多次修改后文件内容已变化。

### 修复方案

在执行多次 patch 前，**先用 `read_file` 重新读取最新文件内容**，确认 old_string 在当前版本中仍然存在，再执行 patch。

---

*本文件为技术陷阱经验库，持续更新。*
