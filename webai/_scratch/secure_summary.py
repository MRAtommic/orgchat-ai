import re

filepath = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\routes\chat.py"

# Open with ignore to preserve whatever encoding it has
with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Let's find the exact block for generate_global_summary and replace it
target_pattern = """@chat_bp.route("/api/summary/generate", methods=["POST"])
@login_required
def generate_global_summary():
    data = request.json or {}
    focus = data.get("focus", "").strip()
    category_id = data.get("category_id", "all")

    user = session.get("user", "Admin")
    visible_categories = database.get_categories(user)
    visible_cat_ids = [str(c["id"]) for c in visible_categories]

    # Global visibility filter (user sees visible categories + unassigned)
    global_where = {
        "$or": [
            {"category_id": {"$in": visible_cat_ids}},
            {"category_id": ""}
        ]
    }

    where_filter = None
    search_query = focus

    if category_id != "all":
        if category_id == "unassigned":
            where_filter = {"category_id": ""}
            if not search_query: search_query = ""
        else:
            if str(category_id) not in visible_cat_ids:
                return jsonify({"ok": False, "error": ""}), 403
            where_filter = {"category_id": str(category_id)}
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
    # else: category_id == "all"  where_filter stays None (search ALL data)

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

        # Fallback 2: Try without any filter at all
        if not results and where_filter is not None:
            print(f" Filtered search empty, falling back to unfiltered search")
            results = rag_engine.search_kb(search_query, n_results=10)
            if not results:
                results = rag_engine.get_all_chunks(limit=10)
            is_fallback = True

        if not results:
            msg = ""
            return jsonify({"ok": False, "error": msg}), 404"""

# Normalize whitespaces and carriage returns to ensure exact matching
target_pattern_norm = "\n".join([line.rstrip() for line in target_pattern.splitlines()])

content_norm = "\n".join([line.rstrip() for line in content.splitlines()])

# Replacement content
replacement = """@chat_bp.route("/api/summary/generate", methods=["POST"])
@login_required
def generate_global_summary():
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

replacement_norm = "\n".join([line.rstrip() for line in replacement.splitlines()])

if target_pattern_norm in content_norm:
    new_content = content_norm.replace(target_pattern_norm, replacement_norm)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: Summary API secured successfully!")
else:
    print("ERROR: Target pattern not found exactly in routes/chat.py!")
