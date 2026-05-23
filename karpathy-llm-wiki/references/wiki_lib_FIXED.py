"""
karpathy-llm-wiki 核心库 FIXED 版
修复：
1. _scan_wiki_pages() 现在正确提取 frontmatter（之前漏了这步）
2. wiki_lint() 使用 updated 而非 last_updated
3. _get_fm() 保留，遇到无 frontmatter 文件返回 {}

使用方式：
- 全局目录: C:/Users/Administrator/.hermes/skills/karpathy-llm-wiki/wiki_lib.py
- Profile目录: C:/Users/Administrator/.hermes/profiles/land-of-dream-planning/skills/karpathy-llm-wiki/wiki_lib.py
复制此文件内容覆盖上述两处 wiki_lib.py 即可完成修复。
"""

import pathlib, re, json
from datetime import datetime, date
from typing import Optional

WIKI_ROOT = pathlib.Path("E:/Landofdream/wiki")
RAW_DIR = WIKI_ROOT / "raw"
INDEX_FILE = WIKI_ROOT / "index.md"
LOG_FILE = WIKI_ROOT / "log.md"
SCHEMA_FILE = WIKI_ROOT / "SCHEMA.md"


def _today() -> str:
    return date.today().isoformat()


def _get_fm(content: str) -> dict:
    """从 markdown 内容中提取 YAML frontmatter"""
    match = re.search(r"(?s)^---\n(.+?)\n---", content)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        kv = line.split(":", 1)
        if len(kv) == 2:
            fm[kv[0].strip()] = kv[1].strip()
    return fm


def _scan_wiki_pages() -> dict:
    """扫描 wiki 目录下所有 .md 文件，排除 raw/ 和 _archive/"""
    pages = {}
    skip_dirs = {"raw", "_archive", ".obsidian"}
    for f in WIKI_ROOT.rglob("*.md"):
        if any(d in f.parts for d in skip_dirs):
            continue
        rel = f.relative_to(WIKI_ROOT).as_posix()
        content = f.read_text(encoding="utf-8")
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)
        headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
        fm = _get_fm(content)
        pages[rel] = {
            "path": str(f),
            "rel": rel,
            "links_out": wikilinks,
            "headings": headings,
            "frontmatter": fm,
            "size": len(content),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
        }
    return pages


def _build_link_graph(pages: dict) -> dict:
    inlinks: dict = {p: [] for p in pages}
    for src, info in pages.items():
        for target in info["links_out"]:
            target_clean = target.split("#")[0].strip()
            if target_clean and target_clean in inlinks:
                inlinks[target_clean].append(src)
    return inlinks


def _log_append(action: str, subject: str, detail: str = "") -> None:
    entry = f"\n## [{_today()}] {action} | {subject}\n"
    if detail:
        entry += detail + "\n"
    LOG_FILE.write_text(LOG_FILE.read_text(encoding="utf-8") + entry, encoding="utf-8")


def _index_append(filename: str, title: str, category: str) -> None:
    link = filename.replace(".md", "")
    new_line = f"- [[{link}]] — {title}\n"
    idx_content = INDEX_FILE.read_text(encoding="utf-8")
    idx_content += new_line
    INDEX_FILE.write_text(idx_content, encoding="utf-8")


def wiki_lint(focus_on: Optional[str] = None) -> dict:
    pages = _scan_wiki_pages()
    inlinks = _build_link_graph(pages)
    orphans = []
    stale = []
    for rel, info in pages.items():
        if focus_on and focus_on not in rel:
            continue
        if not info["links_out"] and not inlinks[rel]:
            orphans.append(rel)
    for rel, info in pages.items():
        if focus_on and focus_on not in rel:
            continue
        lu = info["frontmatter"].get("updated", "")   # ← 修复：之前误用 last_updated
        if lu and re.match(r"\d{4}-\d{2}-\d{2}", lu):
            file_date = info["modified"]
            if lu < file_date:
                days = (datetime.strptime(file_date, "%Y-%m-%d") - datetime.strptime(lu, "%Y-%m-%d")).days
                if days > 7:
                    stale.append({"page": rel, "frontmatter_date": lu, "file_modified": file_date, "days_behind": days})
    total = len(pages)
    orphan_n = len(orphans)
    stale_n = len(stale)
    msg = (
        f"体检完成。共 {total} 个页面。"
        f"孤立 {orphan_n} 个" + (f"：{orphans[:5]}" + ("..." if len(orphans) > 5 else "") if orphan_n else "（无）")
        + "。过时 " + str(stale_n) + " 个" + (f"：{[s['page'] for s in stale[:3]]}" if stale_n else "（无）")
    )
    print(msg)
    return {"orphans": orphans, "stale": stale, "total_pages": total, "summary": msg, "checked_at": _today()}


def wiki_query(keyword: str, limit: int = 5) -> dict:
    pages = _scan_wiki_pages()
    keyword_lower = keyword.lower()
    matches = []
    for rel, info in pages.items():
        score = 0
        match_reason = ""
        if keyword_lower in rel.lower():
            score = 10
            match_reason = "文件名匹配"
        else:
            content = pathlib.Path(info["path"]).read_text(encoding="utf-8")
            count = content.lower().count(keyword_lower)
            if count > 0:
                score = count
                match_reason = f"内容命中 {count} 次"
                first_para = content.split("\n\n")[0][:150] if "\n\n" in content else content[:150]
                matches.append({**info, "score": score, "match_reason": match_reason, "preview": first_para})
                continue
        if score > 0:
            matches.append({**info, "score": score, "match_reason": match_reason})
    matches.sort(key=lambda x: x["score"], reverse=True)
    print(f"QUERY '{keyword}': 找到 {len(matches)} 条匹配，显示前 {min(limit, len(matches))} 条")
    for m in matches[:limit]:
        print(f"  [{m['score']}pts] {m['rel']} — {m.get('match_reason','')}")
    return {"query": keyword, "matches": matches[:limit], "count": len(matches), "searched_at": _today()}


def wiki_ingest(source_path: str, category: str = "articles",
                title: Optional[str] = None,
                tags: Optional[list] = None,
                dry_run: bool = False) -> dict:
    source = pathlib.Path(source_path)
    if not source.is_absolute():
        source = WIKI_ROOT / source
    if not source.exists():
        return {"error": f"文件不存在: {source}"}
    ext = source.suffix.lower()
    if ext == ".md":
        content = source.read_text(encoding="utf-8")
    elif ext == ".txt":
        content = source.read_text(encoding="utf-8")
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(source))
            content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except ImportError:
            return {"error": "python-docx 未安装，无法读取 .docx"}
    else:
        content = f"[非文本文件: {ext}]，仅记录文件名"
    if not title:
        first_line = content.strip().split("\n")[0]
        title = first_line.lstrip("#").strip() if first_line.startswith("#") else source.stem.replace("-", " ").replace("_", " ").strip()
    slug = re.sub(r"[^\w\-]", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")[:60]
    dest_file = WIKI_ROOT / "entities" / f"{slug}.md"
    if dest_file.exists() and not dry_run:
        return {"error": f"页面已存在: {dest_file.name}，请先 archive 或手动确认"}
    fm_tags = tags or [category, "ingested"]
    frontmatter = f"""---
title: "{title}"
source: "{source.relative_to(WIKI_ROOT) if source.is_relative_to(WIFI_ROOT) else str(source)}"
category: {category}
tags: [{", ".join(fm_tags)}]
created: {_today()}
updated: {_today()}
---

# {title}

"""
    if not dry_run:
        dest_file.write_text(frontmatter + content[:5000], encoding="utf-8")
        _index_append(dest_file.name, title, "entities")
        _log_append("ingest", title, f"- 来源：`{source}`")
    return {
        "action": "ingest" + ("(dry-run)" if dry_run else ""),
        "source": str(source),
        "page": str(dest_file.relative_to(WIKI_ROOT)),
        "title": title,
        "content_preview": content[:200] if len(content) > 200 else content,
    }


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lint"
    if cmd == "lint":
        result = wiki_lint()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "query":
        kw = sys.argv[2] if len(sys.argv) > 2 else "理想之地"
        result = wiki_query(kw)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "ingest":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        result = wiki_ingest(path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"未知命令: {cmd}，可用: lint / query <关键词> / ingest <路径>")
