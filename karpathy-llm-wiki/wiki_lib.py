"""
karpathy-llm-wiki 核心库 — 多 vault 版
同时支持：理想之地（E:/Landofdream/wiki）
          AIGC-KB  （E:/AIGC-KB/wiki）
"""

import pathlib, re, json
from datetime import datetime, date
from typing import Optional, Literal

VAULTS = {
    "理想之地":  pathlib.Path("E:/Landofdream/wiki"),
    "AIGC-KB":   pathlib.Path("E:/AIGC-KB/wiki"),
}
DEFAULT = "理想之地"


def _vault(key: Optional[str] = None) -> pathlib.Path:
    return VAULTS.get(key or DEFAULT, VAULTS[DEFAULT])


def _today() -> str:
    return date.today().isoformat()


def _get_fm(content: str) -> dict:
    match = re.search(r"(?s)^---\n(.+?)\n---", content)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        kv = line.split(":", 1)
        if len(kv) == 2:
            fm[kv[0].strip()] = kv[1].strip()
    return fm


def _scan(vault_root: pathlib.Path, skip_dirs=None) -> dict:
    if skip_dirs is None:
        skip_dirs = {"raw", "_archive", ".obsidian", "node_modules", ".pnpm"}
    pages = {}
    for f in vault_root.rglob("*.md"):
        if any(d in f.parts for d in skip_dirs):
            continue
        rel = f.relative_to(vault_root).as_posix()
        content = f.read_text(encoding="utf-8")
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)
        headings  = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
        fm        = _get_fm(content)
        pages[rel] = {
            "path": str(f),
            "rel":  rel,
            "links_out": wikilinks,
            "headings":  headings,
            "frontmatter": fm,
            "size": len(content),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
        }
    return pages


def _build_inlinks(pages: dict) -> dict:
    inlinks = {p: [] for p in pages}
    for src, info in pages.items():
        for target in info["links_out"]:
            t = target.split("#")[0].strip()
            if t and t in inlinks:
                inlinks[t].append(src)
    return inlinks


def _log_append(vault_root: pathlib.Path, action: str, subject: str, detail: str = "") -> None:
    log_file = vault_root / "log.md"
    entry = f"\n## [{_today()}] {action} | {subject}\n"
    if detail:
        entry += detail + "\n"
    log_file.write_text(log_file.read_text(encoding="utf-8") + entry, encoding="utf-8")


def _index_append(vault_root: pathlib.Path, filename: str, title: str, category: str) -> None:
    idx = vault_root / "index.md"
    link = filename.replace(".md", "")
    new_line = f"- [[{link}]] — {title}\n"
    idx.write_text(idx.read_text(encoding="utf-8") + new_line, encoding="utf-8")


# ── 对外 API ────────────────────────────────────────────────

def wiki_lint(vault: Optional[str] = None, focus_on: Optional[str] = None) -> dict:
    """体检指定 vault 或默认 vault"""
    vr = _vault(vault)
    pages   = _scan(vr)
    inlinks = _build_inlinks(pages)
    orphans, stale = [], []

    for rel, info in pages.items():
        if focus_on and focus_on not in rel:
            continue
        if not info["links_out"] and not inlinks[rel]:
            orphans.append(rel)

    for rel, info in pages.items():
        if focus_on and focus_on not in rel:
            continue
        lu = info["frontmatter"].get("updated", "")
        if lu and re.match(r"\d{4}-\d{2}-\d{2}", lu):
            file_date = info["modified"]
            if lu < file_date:
                days = (datetime.strptime(file_date, "%Y-%m-%d") - datetime.strptime(lu, "%Y-%m-%d")).days
                if days > 7:
                    stale.append({"page": rel, "frontmatter_date": lu,
                                  "file_modified": file_date, "days_behind": days})

    total = len(pages)
    msg = (f"[{vault or DEFAULT}] 体检完成，共 {total} 个页面。"
           f" 孤立 {len(orphans)} 个" + (f"：{orphans[:5]}" if orphans else "（无）")
           + f"。过时 {len(stale)} 个" + (f"：{[s['page'] for s in stale[:3]]}" if stale else "（无）"))

    print(msg)
    return {"vault": vault or DEFAULT, "orphans": orphans, "stale": stale,
            "total_pages": total, "summary": msg, "checked_at": _today()}


def wiki_query(keyword: str, vault: Optional[str] = None, limit: int = 5) -> dict:
    """在指定 vault（默认双 vault）搜索关键词"""
    results_all = {}
    targets = [vault] if vault else list(VAULTS.keys())

    for vk in targets:
        vr      = VAULTS[vk]
        pages   = _scan(vr)
        kw_lower = keyword.lower()
        matches = []

        for rel, info in pages.items():
            score = 0
            reason = ""
            if kw_lower in rel.lower():
                score, reason = 10, "文件名命中"
            else:
                content = pathlib.Path(info["path"]).read_text(encoding="utf-8")
                count = content.lower().count(kw_lower)
                if count > 0:
                    score, reason = count, f"内容 {count} 次"
                    preview = content.split("\n\n")[0][:150] if "\n\n" in content else content[:150]
                    matches.append({**info, "score": score, "match_reason": reason, "preview": preview})
                    continue
            if score > 0:
                matches.append({**info, "score": score, "match_reason": reason})

        matches.sort(key=lambda x: x["score"], reverse=True)
        results_all[vk] = {"matches": matches[:limit], "total": len(matches)}

    # 打印摘要
    for vk, res in results_all.items():
        shown = res["matches"]
        print(f"\n## [{vk}] 「{keyword}」— {res['total']} 条匹配，显示前 {len(shown)} 条")
        for m in shown:
            print(f"  [{m['score']}pts] {m['rel']} — {m['match_reason']}")

    return {"query": keyword, "results": results_all, "searched_at": _today()}


def wiki_ingest(source_path: str, vault: Optional[str] = None,
                 category: str = "articles",
                 title: Optional[str] = None,
                 tags: Optional[list] = None,
                 dry_run: bool = False) -> dict:
    """摄入文件到指定 vault"""
    vr = _vault(vault)
    source = pathlib.Path(source_path)
    if not source.is_absolute():
        source = vr / source

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
            content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            return {"error": "python-docx 未安装"}
    else:
        content = f"[非文本文件: {ext}]"

    if not title:
        first = content.strip().split("\n")[0]
        title = first.lstrip("#").strip() if first.startswith("#") else source.stem.replace("-", " ").replace("_", " ").strip()

    slug = re.sub(r"[^\w\-]", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")[:60]

    dest_file = vr / "entities" / f"{slug}.md"
    if dest_file.exists() and not dry_run:
        return {"error": f"页面已存在: {dest_file.name}，请先 archive"}

    fm_tags = tags or [category, "ingested"]
    frontmatter = f"""---
title: "{title}"
source: "{source.relative_to(vr) if source.is_relative_to(vr) else str(source)}"
category: {category}
tags: [{", ".join(fm_tags)}]
created: {_today()}
updated: {_today()}
---

# {title}

"""
    if not dry_run:
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(frontmatter + content[:5000], encoding="utf-8")
        _index_append(vr, dest_file.name, title, "entities")
        _log_append(vr, "ingest", title, f"- 来源：`{source}`")

    return {"action": "ingest" + ("(dry-run)" if dry_run else ""),
            "vault": vault or DEFAULT, "source": str(source),
            "page": str(dest_file.relative_to(vr)), "title": title}


def vault_status(vault: Optional[str] = None) -> dict:
    """列出所有 vault 状态"""
    if vault:
        vkeys = [vault]
    else:
        vkeys = list(VAULTS.keys())

    status = {}
    for vk in vkeys:
        vr    = VAULTS[vk]
        pages = _scan(vr)
        status[vk] = {
            "root": str(vr),
            "total_pages": len(pages),
            "exists": vr.exists(),
        }
        idx = vr / "index.md"
        status[vk]["has_index"] = idx.exists()
        log = vr / "log.md"
        status[vk]["has_log"] = log.exists()

    for vk, s in status.items():
        print(f"\n## {vk}")
        print(f"   路径: {s['root']}")
        print(f"   存在: {s['exists']} | index.md: {s['has_index']} | log.md: {s['has_log']}")
        print(f"   页面数: {s['total_pages']}")

    return status


if __name__ == "__main__":
    import sys
    cmd   = sys.argv[1] if len(sys.argv) > 1 else "status"
    vault = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "lint":
        result = wiki_lint(vault)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "query":
        kw = sys.argv[2] if len(sys.argv) > 2 else "理想之地"
        v  = sys.argv[3] if len(sys.argv) > 3 else None
        result = wiki_query(kw, v)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "ingest":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        v    = sys.argv[3] if len(sys.argv) > 3 else None
        result = wiki_ingest(path, v)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "status":
        result = vault_status(vault)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"未知命令: {cmd}，可用: lint / query <关键词> / ingest <路径> / status")
