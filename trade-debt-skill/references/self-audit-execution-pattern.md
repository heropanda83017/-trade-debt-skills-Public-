# 知识库自检执行模式（TradeDebt 专用）

> **来源：** 2026-05-23 首次全面自检实战记录
> **关联技能章节：** trade-debt-skill 第十二节（知识库自检与治理框架）
> **触发词：** 「自检」「llm wiki 扫描」「体检」「全身体检」

## 一、前置条件

| 条件 | 说明 |
|------|------|
| 工作目录 | `E:\TradeDebt\`（WSL: `/mnt/e/TradeDebt/`） |
| 工具限制 | `read_file` / `patch` 在 `C:\Users\Administrator\.hermes\` 路径下不可用 → 改用 `execute_code` + Python `open()` |
| 搜索限制 | `search_files`（rg）不可用 → 改用 `execute_code` + `os.walk()` |

## 二、五层扫描代码模板

### Layer 0 — 目录结构总览

```python
from pathlib import Path
BASE = Path(r"E:\TradeDebt")
for p in sorted(BASE.iterdir()):
    if p.is_dir():
        sub = list(p.iterdir())
        print(f"  {p.name}/ ({len(sub)}项)")
```

### Layer 1 — Wiki 页面质量

```python
WIKI = BASE / "wiki"
all_md = list(WIKI.rglob("*.md"))
for p in all_md:
    rel = p.relative_to(WIKI)
    size = p.stat().st_size / 1024
    content = p.read_text(encoding='utf-8', errors='replace')
    # 检查 frontmatter 完整性
    has_fm = content.startswith('---')
    # 检查 wikilink 出链
    links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    # 检查入链（反向索引）
    ...
```

### Layer 2 — 目录文件覆盖率

```python
source_subdirs = [
    "01-债务人档案", "02-债权凭证", "03-法律文书", "04-催收记录",
    "05-数据分析", "06-策略方案", "07-政策法规", "08-汇报材料", "09-参考素材"
]
for sd in source_subdirs:
    p = BASE / "源文件" / sd
    items = list(p.iterdir()) if p.exists() else []
    print(f"  {sd}/: {len(items)}项")
```

### Layer 3 — SOUL.md + skill 路径索引验证（关键）

```python
soul_path = r"C:\Users\Administrator\.hermes\profiles\trade-debt\SOUL.md"
skill_path = r"C:\Users\Administrator\.hermes\profiles\trade-debt\skills\trade-debt-skill\SKILL.md"

# 1. 检查 SOUL.md 文件保存规范中路径前缀是否使用 `源文件\`
# 2. 提取 skill 第六节所有文件路径，用 os.path.exists() 验证
# 3. 特别关注：催收报告可能在 04-催收记录 而非 02-债权凭证
for root, dirs, files in os.walk(str(BASE)):
    for f in files:
        if '催收最新情况' in f and 'V2.0' in f:
            print(f"  ✅ {os.path.join(root, f)}")
```

## 三、2026-05-23 首次自检发现的 P0 问题

| # | 问题 | 修复方式 | 影响文件 |
|---|------|---------|---------|
| 1 | skill 第六节8处路径指向根目录，实际在 `源文件/` 下 | 路径替换为 `源文件/` 前缀 | `skills/trade-debt-skill/SKILL.md` |
| 2 | 催收报告V2.0被索引到02-债权凭证，实际在04-催收记录 | 修正索引路径和分类 | `SKILL.md` 第248-249行 |
| 3 | 02-债权凭证、06-策略方案目录缺失 | 新建目录 | 文件系统 |
| 4 | wiki/log.md 无 frontmatter（管理页，接受） | 不修复 | — |
| 5 | SOUL.md 路径已正确指向 `源文件/` | 无需修复 | — |

## 四、常见陷阱

| 陷阱 | 表现 | 避免方法 |
|------|------|---------|
| 路径前缀错层 | skill 索引用 `E:\TradeDebt\01\...` 但实际在 `E:\TradeDebt\源文件\01\...` | Layer 3 必做路径可达性验证 |
| 文件分类错位 | 催收报告属于 `04-催收记录` 但被索引到 `02-债权凭证` | 确认文件所在目录与其内容分类一致 |
| 文件移动后未更新索引 | 文件挪动了但 skill 索引还是旧路径 | 每次文件操作后运行一次完整自检 |
