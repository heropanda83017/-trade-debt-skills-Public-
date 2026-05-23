---
name: html-report-to-visual-faithful-pdf
description: 当 Chrome print-to-pdf 导致 HTML 报告字段裁切、最后一页渲染失败、A4分页压缩或上下排版变差时，使用“逐 slide 截图 + 图片组装 PDF”的视觉保真方案。
trigger: HTML报告转PDF失败、PDF渲染失败、最后一页空白、字段不显示、表格被裁切、A4压缩排版难看、需要视觉保真PDF
---

# HTML 报告转视觉保真 PDF

## 适用场景

当用户要求把本地 HTML/H5 报告转 PDF，但常规 Chrome `--print-to-pdf` 出现以下问题时使用：

- 表格字段没有显示完整，被横向滚动容器裁切。
- 最后一页渲染失败、大片空白、只剩页眉或内容错位。
- 为了适配 A4/A3 打印，页面被上下压缩，排版很差。
- 原报告是 slide/card/dashboard 风格，更需要“看起来和 HTML 一样”，而不是可搜索文本。

该方案优先保证视觉稳定和排版保真；缺点是最终 PDF 为图片层，文字不可搜索。

## 核心思路

不要让 Chrome print 引擎直接对整份长 HTML 分页。

改为：
1. 用 Playwright 打开原始 HTML。
2. 逐个定位 `section.slide` 或主要页面容器。
3. 对每个 slide 做元素截图，保留自然高度。
4. 用 PIL 将每张截图按自然尺寸组装成多页 PDF。
5. 自检每页尺寸、上下空白和最后一页截图。

这样可以绕开 print-to-pdf 的分页、overflow、表格滚动和最后一页渲染问题。

## 前置条件

- macOS + Google Chrome：`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Python Playwright 可用：`from playwright.async_api import async_playwright`
- Pillow 可用：`from PIL import Image`

若 Node 版 Playwright 不可用，不要卡住；优先用 Python Playwright。

## 推荐输出命名

文件名必须简洁，直接写“主题 + 日期/时间戳”，不要把实现方式、风格词、过程词写进文件名。

推荐：
- HTML：`主题_YYYYMMDD.html`
- PDF：`主题_YYYYMMDD.pdf`
- 逐页 PNG 目录：`主题_YYYYMMDD_pages/`
- 逐页 PNG：`page_01.png`、`page_02.png` ...

禁止/避免：
- `PPT`、`iOS`、`视觉保真`、`FINAL`、`新版`、`正式版` 等废话后缀，除非用户明确要求。
- 例如不要写：`朱水境_简历与初面评估报告_PPT_iOS_视觉保真_20260511.pdf`
- 应写：`朱水境_简历与初面评估报告_20260511.pdf`

## 渲染脚本模板

```python
from hermes_tools import write_file, terminal
import os

html = '/path/to/report_FINAL.html'
outdir = '/path/to/pdf_visual_pages'
os.makedirs(outdir, exist_ok=True)
script = os.path.join(outdir, 'render_visual_pages.py')

py = r'''
import asyncio, sys, os, json
from playwright.async_api import async_playwright

CSS = """
html, body { background:#eef2f6 !important; }
.deck { max-width:1480px !important; padding:24px !important; gap:24px !important; }
.slide { overflow:visible !important; min-height:auto !important; height:auto !important; page-break-after:auto !important; }
.table-wrapper { overflow:visible !important; max-width:none !important; }
table { min-width:0 !important; width:100% !important; table-layout:auto !important; }
th, td { white-space:normal !important; word-break:break-word !important; overflow-wrap:anywhere !important; }
@media print { .cover{display:flex!important}.slide{min-height:auto!important;overflow:visible!important} }
"""

async def main():
    html_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )
        page = await browser.new_page(viewport={"width":1530,"height":1100}, device_scale_factor=2)
        await page.goto('file://' + html_path, wait_until='networkidle')
        await page.add_style_tag(content=CSS)
        try:
            await page.evaluate("document.fonts && document.fonts.ready")
        except Exception:
            pass

        # 按实际页面结构调整选择器。Hermes/银行报告一般是 section.slide。
        slides = await page.query_selector_all('section.slide')
        if not slides:
            slides = await page.query_selector_all('.slide, .page, .section')
        if not slides:
            slides = [await page.query_selector('body')]

        meta = []
        for i, s in enumerate(slides, 1):
            box = await s.bounding_box()
            path = os.path.join(out_dir, f'page_{i:02d}.png')
            await s.screenshot(path=path)
            meta.append({'i': i, 'box': box, 'path': path})

        await browser.close()
        print(json.dumps({'slides': len(slides), 'meta': meta}, ensure_ascii=False, indent=2))

asyncio.run(main())
'''

write_file(script, py)
res = terminal(f"python3 {script!r} {html!r} {outdir!r}", timeout=180)
print(res['output'])
```

## 图片组装 PDF 模板

```bash
python3 - <<'PY'
from PIL import Image
from pathlib import Path
import json

outdir = Path('/path/to/pdf_visual_pages')
imgs = sorted(outdir.glob('page_*.png'))
pdf = Path('/path/to/report_FINAL_视觉保真.pdf')

pages = []
info = []
for p in imgs:
    im = Image.open(p).convert('RGB')
    # 保留原 slide 内部空白，只加少量外边距；不要强行适配 A4/A3。
    margin = 50
    canvas = Image.new('RGB', (im.width + margin * 2, im.height + margin * 2), (238, 242, 246))
    canvas.paste(im, (margin, margin))
    pages.append(canvas)
    info.append({'file': p.name, 'orig': [im.width, im.height], 'pdf_page': [canvas.width, canvas.height]})

pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=144.0, quality=95)
print(json.dumps({'pdf': str(pdf), 'pages': len(pages), 'info': info, 'size': pdf.stat().st_size}, ensure_ascii=False, indent=2))
PY
```

## 自检脚本

必须自检，不要只说“已生成”。重点检查每页是否被裁切、是否出现巨大上下空白、最后一页是否有内容。

```bash
python3 - <<'PY'
from pathlib import Path
from PIL import Image
import numpy as np, json

outdir = Path('/path/to/pdf_visual_pages')
pdf = Path('/path/to/report_FINAL_视觉保真.pdf')
checks = {'pdf_exists': pdf.exists(), 'pdf_size': pdf.stat().st_size if pdf.exists() else 0, 'images': []}

for p in sorted(outdir.glob('page_*.png')):
    im = Image.open(p).convert('RGB')
    a = np.array(im)
    row_nonwhite = np.mean(np.any(a < 245, axis=2), axis=1)

    top_blank = 0
    for v in row_nonwhite:
        if v < 0.01:
            top_blank += 1
        else:
            break

    bottom_blank = 0
    for v in row_nonwhite[::-1]:
        if v < 0.01:
            bottom_blank += 1
        else:
            break

    checks['images'].append({
        'file': p.name,
        'size': im.size,
        'top_blank_px': int(top_blank),
        'bottom_blank_px': int(bottom_blank),
        'dark_ratio': round(float(np.mean(np.all(a < 130, axis=2))), 4),
        'content_ratio': round(float(np.mean(np.any(a < 245, axis=2))), 4),
    })

print(json.dumps(checks, ensure_ascii=False, indent=2))
PY
```

### 自检判断标准

- 每页 `top_blank_px`、`bottom_blank_px` 不应异常大。若接近 0 是正常的，因为截图对象是 slide 本身。
- `content_ratio` 不应接近 0。接近 0 说明页面空白或截图失败。
- 最后一页必须有正常 `dark_ratio` 和 `content_ratio`，不能只有背景。
- 打开 PDF 和逐页 PNG 目录让用户确认。

## 常见坑

0. **长页面报告不能按每个 section 截图成 PDF**
   - 这是已发生过的严重错误：曾把“朱水境简历与初面评估报告”的 iOS 长页面按每个 section 截图导出 PDF，结果 11 页非常碎片化，一个 KPI/短段落就占一页，被用户批评“至少信息要排版到一个 PPT 页面大的内容中”。以后必须避免。
   - 如果原 HTML 是长滚动报告、iOS 卡片报告，而用户要的是汇报/PPT观感，不能把每个小 section 单独截图成一页；这会导致 PDF 像零散卡片，不像正式汇报材料。
   - 正确做法：先把内容重排成 16:9 PPT-sized slides（例如 `.slide{width:1600px;min-height:900px}`，每页承载一个完整主题），再逐 slide 截图组装 PDF。
   - 每页应有足够信息密度：标题 + 2~4 个信息区块/图表/结论卡，而不是一个小 KPI 或一个短段落就占一页。
   - 导出前先自问：这一页如果投到会议屏幕上，是否像一页完整 PPT？如果不像，必须先重排 HTML，不要直接转 PDF。

1. **不要再用 A4/A3 强制压缩 slide**
   - 这会让上下空间被压扁，排版难看。
   - 视觉保真模式应保持每个 slide 的自然高度。

2. **不要用 `overflow:hidden`**
   - 会导致表格、卡片、最后一页内容被裁切。
   - 截图前应覆盖 `.slide`、`.table-wrapper` 为 `overflow:visible`。

3. **表格不要横向滚动**
   - PDF/截图前应把表格改成 `width:100%; min-width:0; white-space:normal; word-break:break-word`。

4. **这是图片 PDF**
   - 需要文字可搜索时，另做一个“文本版 PDF”；给领导/手机查看优先用视觉保真版。

5. **若用户说手机看不清**
   - 增大 viewport 或 device_scale_factor，例如 width 1530、scale 2 已经较清晰。
   - 也可以输出逐页 PNG 让用户微信发送。

## 最终回复模板

简洁说明：
- 已生成视觉保真 PDF。
- 路径。
- 为什么这版不会再被 A4 压缩/最后页失败。
- 自检结果：页数、文件大小、逐页 PNG 目录、空白/内容检测通过。
