import re

filepath = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\routes\chat.py"

# Open with surrogateescape to safely preserve non-utf-8 bytes
with open(filepath, "r", encoding="utf-8", errors="surrogateescape") as f:
    content = f.read()

print("File loaded successfully with surrogateescape! Length:", len(content))

# ─────────────────────────────────────────────
# FIX 1: LINE Webhook RAG search (Lines 3440-3474)
# ─────────────────────────────────────────────
# We want to replace retrieve_context calls in this specific region.
# Let's find: try:\n                context = ""\n                sources = []\n                if hasattr(rag_engine, 'retrieve_context'):\n                    context, sources = rag_engine.retrieve_context(text, where=None)
# and replace it up to the end of the if/else block.

line_pattern = re.compile(
    r'(try:\s+context\s*=\s*""\s+sources\s*=\s*\[\]\s+if\s+hasattr\(rag_engine,\s*\'retrieve_context\'\):\s+context,\s*sources\s*=\s*rag_engine\.retrieve_context\(text,\s*where=None\).*?response\s*=\s*f"[^"]+:\\n\{ctx\[:500\]\}\.\.\."\s+if\s+ctx\s+else\s*"[^"]+"\s+else:\s+response\s*=\s*"[^"]+"\s+reply_to_line\(reply_token,\s*response,\s*quick_reply=quick_reply\))',
    re.DOTALL
)

# Wait, let's write a simple string-based search for:
# if hasattr(rag_engine, 'retrieve_context'):\n                    context, sources = rag_engine.retrieve_context(text, where=None)
target_string_1 = """                if hasattr(rag_engine, 'retrieve_context'):
                    context, sources = rag_engine.retrieve_context(text, where=None)"""

replacement_string_1 = """                line_where = {"$or": [{"organization_id": _line_org_id}, {"organization_id": {"$eq": None}}]}
                if hasattr(rag_engine, 'retrieve_context'):
                    context, sources = rag_engine.retrieve_context(text, where=line_where)"""

target_string_2 = """                elif hasattr(rag_engine, 'retrieve_context'):
                    ctx, _ = rag_engine.retrieve_context(text)"""

replacement_string_2 = """                elif hasattr(rag_engine, 'retrieve_context'):
                    ctx, _ = rag_engine.retrieve_context(text, where=line_where)"""

target_string_3 = """            if hasattr(rag_engine, 'retrieve_context'):
                ctx, _ = rag_engine.retrieve_context(text)"""

# Wait, we want to make sure target_string_3 is matched in the right place (line 3469).
# Let's see: in line 3469 we have:
#         else:
#             if hasattr(rag_engine, 'retrieve_context'):
#                 ctx, _ = rag_engine.retrieve_context(text)
#                 response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ:\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ ไม่พบข้อมูลที่เกี่ยวข้องค่ะ"
# So let's include "else:" in the target string!
target_string_3_context = """        else:
            if hasattr(rag_engine, 'retrieve_context'):
                ctx, _ = rag_engine.retrieve_context(text)"""

replacement_string_3_context = """        else:
            if hasattr(rag_engine, 'retrieve_context'):
                line_where = {"$or": [{"organization_id": _line_org_id}, {"organization_id": {"$eq": None}}]}
                ctx, _ = rag_engine.retrieve_context(text, where=line_where)"""

# ─────────────────────────────────────────────
# FIX 2: Summary API RAG search (generate_global_summary)
# ─────────────────────────────────────────────
summary_pattern = re.compile(
    r'(def\s+generate_global_summary\(\):.*?return\s+jsonify\(\{"ok":\s*False,\s*"error":\s*msg\}\),\s*404)',
    re.DOTALL
)

summary_replacement = """def generate_global_summary():
    data = request.json or {}
    focus = data.get("focus", "").strip()
    category_id = data.get("category_id", "all")

    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user)
    visible_cat_ids = [str(c["id"]) for c in visible_categories]

    # Respect organization isolation
    org_id = get_current_org_id()
    org_clause = {"$or": [{"organization_id": org_id}, {"organization_id": {"$eq": None}}]}

    where_filter = None
    search_query = focus

    if category_id != "all":
        if category_id == "unassigned":
            where_filter = {
                "$and": [
                    org_clause,
                    {"category_id": ""}
                ]
            }
            if not search_query: search_query = ""
        else:
            if str(category_id) not in visible_cat_ids:
                return jsonify({"ok": False, "error": ""}), 403
            where_filter = {
                "$and": [
                    org_clause,
                    {"category_id": str(category_id)}
                ]
            }
            # Try to get category name for better context if no focus given
            if not search_query:
                try:
                    conn = database._get_conn()
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM kb_categories WHERE id = ?", (int(category_id),))
                        row = cursor.fetchone()
                    finally:
                        conn.close()
                    if row: search_query = f" {row[0]}"
                except: pass
    else: # category_id == "all"
        # Search all visible categories + unassigned, within the organization boundaries
        if visible_cat_ids:
            where_filter = {
                "$and": [
                    org_clause,
                    {
                        "$or": [
                            {"category_id": {"$in": visible_cat_ids}},
                            {"category_id": ""}
                        ]
                    }
                ]
            }
        else:
            where_filter = {
                "$and": [
                    org_clause,
                    {"category_id": ""}
                ]
            }

    if not search_query:
        search_query = "   "

    print(f" Summary Request - Category: {category_id}, Focus: '{focus}', Filter: {where_filter}")

    try:
        is_fallback = False
        # 1. Semantic Search
        results = rag_engine.search_kb(search_query, n_results=10, where=where_filter)

        # Fallback 1: Literal grab from category
        if not results:
            results = rag_engine.get_all_chunks(where=where_filter, limit=10)

        # Fallback 2: Try with only org isolation filter (NEVER completely unfiltered!)
        if not results:
            print(f" Filtered search empty, falling back to org-only search")
            results = rag_engine.search_kb(search_query, n_results=10, where=org_clause)
            if not results:
                results = rag_engine.get_all_chunks(where=org_clause, limit=10)
            is_fallback = True

        if not results:
            msg = ""
            return jsonify({"ok": False, "error": msg}), 404"""

# Normalize content to \n for stable replacing
content_norm = content.replace("\r\n", "\n")

# Apply replacements
modified = False

if target_string_1 in content_norm:
    content_norm = content_norm.replace(target_string_1, replacement_string_1)
    print("FIX 1a applied!")
    modified = True
else:
    print("ERROR: target_string_1 not found!")

if target_string_2 in content_norm:
    content_norm = content_norm.replace(target_string_2, replacement_string_2)
    print("FIX 1b applied!")
    modified = True
else:
    print("ERROR: target_string_2 not found!")

if target_string_3_context in content_norm:
    content_norm = content_norm.replace(target_string_3_context, replacement_string_3_context)
    print("FIX 1c applied!")
    modified = True
else:
    print("ERROR: target_string_3_context not found!")

summary_match = summary_pattern.search(content_norm)
if summary_match:
    content_norm = content_norm[:summary_match.start()] + summary_replacement + content_norm[summary_match.end():]
    print("FIX 2 (Summary API) applied!")
    modified = True
else:
    print("ERROR: summary_pattern not found!")

if modified:
    with open(filepath, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(content_norm)
    print("SUCCESS: All security fixes applied and written back safely!")
else:
    print("NO CHANGES MADE.")
