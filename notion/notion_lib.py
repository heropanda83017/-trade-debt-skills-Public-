"""
Notion API 封装库 - 提供 search / get_page / append_block
"""
import os, json, asyncio
from notion_client import AsyncClient

NOTION_KEY = None
ENV_PATH = os.path.expanduser(r"~\.hermes\.env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            if "NOTION_API_KEY" in line and not line.startswith("#"):
                NOTION_KEY = line.strip().split("=", 1)[1].strip()

def notion_search(query, page_size=10):
    if not NOTION_KEY:
        return {"error": "NOTION_API_KEY not found"}
    async def _search():
        client = AsyncClient(auth=NOTION_KEY)
        try:
            results = await client.search(query=query, page_size=page_size)
            items = []
            for item in results.get("results", []):
                title = ""
                obj_type = item.get("object")
                if obj_type == "page":
                    for pn, pv in item.get("properties", {}).items():
                        if pv.get("type") == "title":
                            title = "".join(t.get("plain_text","") for t in pv.get("title",[]))
                            break
                elif obj_type == "database":
                    title = item.get("title",[{}])[0].get("plain_text","") or "(无标题数据库)"
                items.append({"id": item["id"], "object": obj_type, "title": title or "(无标题)", "last_edited": item.get("last_edited_time","")})
            await client.aclose()
            return {"results": items, "count": len(items)}
        except Exception as e:
            await client.aclose()
            return {"error": str(e)}
    return asyncio.run(_search())

def notion_get_page(page_id):
    if not NOTION_KEY:
        return {"error": "NOTION_API_KEY not found"}
    page_id = page_id.strip()
    async def _get():
        client = AsyncClient(auth=NOTION_KEY)
        try:
            page = await client.pages.retrieve(page_id=page_id)
            blocks = await client.blocks.children.list(block_id=page_id)
            title = ""
            for pn, pv in page.get("properties", {}).items():
                if pv.get("type") == "title":
                    title = "".join(t.get("plain_text","") for t in pv.get("title",[]))
                    break
            content = []
            for block in blocks.get("results", []):
                btype = block.get("type")
                text = ""
                if btype in block:
                    text = "".join(t.get("plain_text","") for t in block[btype].get("rich_text",[]))
                content.append({"type": btype, "text": text})
            await client.aclose()
            return {"id": page["id"], "title": title or "(无标题)", "created": page.get("created_time",""), "last_edited": page.get("last_edited_time",""), "content": content}
        except Exception as e:
            await client.aclose()
            return {"error": str(e)}
    return asyncio.run(_get())

def notion_append_block(page_id, content_text, block_type="paragraph"):
    if not NOTION_KEY:
        return {"error": "NOTION_API_KEY not found"}
    page_id = page_id.strip()
    type_map = {"paragraph":"paragraph","heading_1":"heading_1","heading_2":"heading_2","bulleted_list_item":"bulleted_list_item"}
    notion_type = type_map.get(block_type, "paragraph")
    async def _append():
        client = AsyncClient(auth=NOTION_KEY)
        try:
            result = await client.blocks.children.append(block_id=page_id, children=[{"object":"block","type":notion_type,notion_type:{"rich_text":[{"type":"text","text":{"content":content_text}}]}}])
            await client.aclose()
            return {"success": True, "block_id": result.get("results",[{}])[0].get("id","")}
        except Exception as e:
            await client.aclose()
            return {"error": str(e)}
    return asyncio.run(_append())

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "search":
        print(json.dumps(notion_search(sys.argv[2] if len(sys.argv)>2 else ""), ensure_ascii=False, indent=2))
    elif cmd == "get":
        print(json.dumps(notion_get_page(sys.argv[2] if len(sys.argv)>2 else ""), ensure_ascii=False, indent=2))
    elif cmd == "append":
        print(json.dumps(notion_append_block(sys.argv[2] if len(sys.argv)>2 else "", sys.argv[3] if len(sys.argv)>3 else ""), ensure_ascii=False, indent=2))
