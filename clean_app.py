import os
import re
import py_compile

def clean_file():
    file_path = "app_server.py"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found in current directory.")
        return

    print("==================================================")
    print("      OrgChat AI - App Server Sanitizer v5.0      ")
    print("==================================================")

    # Read the file with errors='ignore' to automatically strip invalid UTF-8 byte sequences
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    print(f"Loaded {file_path} ({len(content)} characters).")

    # Replacement 0A: Bypassed as committed code is clean and contains the legitimate Kanban status block
    print("[✔] Bypassed Replacement 0A (Committed Kanban status block is clean and legitimate).")

    # Replacement 0B: Fix duplicate field_rows.append in create_line_flex_bubble (line 846 approx)
    idx_start = content.find('def create_line_flex_bubble(title, subtitle, fields, color="#1DB446"):')
    idx_end = content.find('def send_line_push_notification(target_username, title, text, fields=None):')
    if idx_start != -1 and idx_end != -1:
        flex_replacement = """def create_line_flex_bubble(title, subtitle, fields, color="#1DB446"):
    \"\"\"Creates a beautiful LINE Flex Message JSON bubble.\"\"\"
    contents = []
    contents.append({"type": "text", "text": title, "weight": "bold", "size": "xl", "color": color})
    if subtitle:
        contents.append({"type": "text", "text": subtitle, "size": "sm", "color": "#aaaaaa", "wrap": True, "margin": "md"})
    contents.append({"type": "separator", "margin": "lg"})
    
    field_rows = []
    for key, val in fields.items():
        field_rows.append({
            "type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": key, "size": "sm", "color": "#555555", "flex": 1},
                {"type": "text", "text": str(val), "size": "sm", "color": "#111111", "flex": 2, "wrap": True}
            ]
        })
    contents.append({"type": "box", "layout": "vertical", "contents": field_rows, "margin": "lg"})
    contents.append({"type": "separator", "margin": "lg"})
    contents.append({"type": "text", "text": "OrgChat Smart Helper", "size": "xs", "color": "#aaaaaa", "align": "end", "style": "italic", "margin": "md"})

    return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": contents}}

\n\n"""
        content = content[:idx_start] + flex_replacement + content[idx_end:]
        print("[✔] Sanitized create_line_flex_bubble syntax error.")
    else:
        print("[❌] Failed to find create_line_flex_bubble anchors.")

    # Replacement 1: LINE bot handle_message exception block
    idx_start = content.find('except Exception as e:\n                logger.error(f"AI Generation failed: {e}")')
    idx_end = content.find('@app.route("/api/admin/line/broadcast"')
    if idx_start != -1 and idx_end != -1:
        replacement = """except Exception as e:
                logger.error(f"AI Generation failed: {e}")
                if 'context' in locals() and context:
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\\n{context[:500]}..."
                elif hasattr(rag_engine, 'retrieve_context'):
                    ctx, _ = rag_engine.retrieve_context(text)
                    response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ (สำรอง):\\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                else:
                    response = "ขออภัยนะคะ พั้นมีปัญหาในการดึงข้อมูลสักครู่ ลองใหม่อีกครั้งนะคะ"
                reply_to_line(reply_token, response, quick_reply=quick_reply)
        else:
            if hasattr(rag_engine, 'retrieve_context'):
                ctx, _ = rag_engine.retrieve_context(text)
                response = f"พั้นเจอข้อมูลที่เกี่ยวข้องดังนี้ค่ะ:\\n{ctx[:500]}..." if ctx else "ขออภัยนะคะ ไม่พบข้อมูลที่เกี่ยวข้องค่ะ"
            else:
                response = "ระบบ AI ยังไม่พร้อมใช้งานในขณะนี้ค่ะ"
            reply_to_line(reply_token, response, quick_reply=quick_reply)

    except Exception as e:
        logger.error(f"Command processing failed: {e}")
        reply_to_line(reply_token, "ขออภัยนะคะ เกิดข้อผิดพลาดในการประมวลผลข้อมูล ลองใหม่อีกครั้งนะคะ", quick_reply=quick_reply)

\n\n"""
        content = content[:idx_start] + replacement + content[idx_end:]
        print("[✔] Sanitized LINE bot exception block.")
    else:
        print("[❌] Failed to find LINE bot exception block anchors.")

    # Replacement 2: Chat Route API
    idx_start = content.find('@app.route("/api/chat", methods=["POST"])')
    idx_end = content.find('@app.route("/api/chat/typing", methods=["POST"])')
    if idx_start != -1 and idx_end != -1:
        chat_replacement = """@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    provider = os.environ.get("AI_PROVIDER", "groq").lower()
    api_key = _get_gemini_api_key() if provider == "gemini" else True
    print(f"Chat request received. Provider: {provider}. API Key present: {bool(api_key)}")
    if not api_key:
        return jsonify({"ok": False, "error": "ยังไม่ได้ตั้งค่า Gemini API Key"}), 400

    data = request.get_json(force=True)
    import time
    t0 = time.time()
    
    question = (data.get("message") or "").strip()
    history = data.get("history", [])
    persona_id = data.get("persona_id")
    image_data_raw = data.get("image_data")
    mime_type = data.get("mime_type", "image/jpeg")

    image_bytes = None
    if image_data_raw:
        try:
            import base64
            if "," in image_data_raw:
                header, image_data_raw = image_data_raw.split(",", 1)
                if "mime_type" not in data and "image/" in header:
                    mime_type = header.split(":")[1].split(";")[0]
            
            image_bytes = base64.b64decode(image_data_raw)
            print(f"Image received: {len(image_bytes)} bytes. Mime: {mime_type}")
        except Exception as e:
            print(f"Error decoding image: {e}")

    if not question and not image_bytes:
        return jsonify({"ok": False, "error": "กรุณาพิมพ์คำถามหรือส่งรูปภาพค่ะ"}), 400

    current_user = session.get("user", "Admin")

    import re
    rag_filter = get_rag_filter(current_user)
    
    file_match = re.search(r"ช่วยสรุปเนื้อหาและศึกษาข้อมูลสำคัญจากไฟล์ ID:\\s*([a-f0-9\\-]+)", question)
    if file_match:
        file_id = file_match.group(1).strip()
        print(f"Detected File Summary Request for ID: {file_id}")
        
        file_filter = {"file_id": file_id}
        if rag_filter:
            file_filter = {"$and": [rag_filter, {"file_id": file_id}]}
            
        chunks = rag_engine.get_all_chunks(limit=50, where=file_filter)
        
        context_parts = []
        sources = []
        seen_s = set()
        
        for r in chunks:
            loc = r.get("location", "Document")
            dept = r.get("department", "General")
            src = r.get("source", "?")
            fid = r.get("file_id", str(file_id))
            
            context_parts.append(f"--- แหล่งที่มา: {src} [{loc}] (File ID: {fid}) ---\\n{r.get('text', '')}")
            
            s_key = f"{fid}_{loc}"
            if s_key not in seen_s:
                sources.append({"file_id": str(fid), "name": src, "location": loc, "department": dept, "type": r.get("type", "file")})
                seen_s.add(s_key)
                
        context = "\\n\\n".join(context_parts)
        if sources:
            file_name = sources[0]["name"]
            question += f"\\n(ระบบดึงข้อมูล 50 ส่วนแรกจากไฟล์ '{file_name}' มาให้พิจารณาแล้ว ใน context นี้ เพื่อสรุปภาพรวมให้ค่ะ)"
    else:
        context, sources = "", []
        common_greets = ["สวัสดี", "หวัดดี", "ว่าไง", "ทักทาย", "hi", "hello", "hey"]
        is_greeting = any(g in (question or "").lower() for g in common_greets)
        
        if question and len(question) > 5 and not is_greeting:
            import sys
            rag_filter = get_rag_filter(current_user)
            context, sources = rag_engine.retrieve_context(question, where=rag_filter)
            print(f"DEBUG: RAG Retrieval took {time.time() - t0:.3f}s", flush=True)
            sys.stdout.flush()
        else:
            context, sources = "", []
            if is_greeting: 
                print("Fast Path: Skipping RAG", flush=True)
                import sys; sys.stdout.flush()

    now_str = get_current_time()
    
    persona_prompt = ""
    persona_name = "AI Assistant"
    if persona_id:
        persona = database.get_persona(persona_id)
        if persona:
            persona_prompt = persona.get("system_prompt", "")
            persona_name = persona.get("name", "AI Assistant")

    agentic_info = (
        f"\\n[สำคัญ] วันนี้คือวันที่ {now_str}. หากผู้ใช้งานบันทึกวันที่ (เช่น พรุ่งนี้, วันจันทร์หน้า) ให้คุณแปลงเป็นวันที่จริง (YYYY-MM-DD) ออกมาให้ถูกต้อง\\n"
        "หากผู้ใช้งานต้องการ 'นัดหมาย' 'จองคิว' 'แจ้งเตือน' หรือ 'สร้างงาน' ให้คุณสรุปงานเป็น JSON ภายใต้คำขอโดยใช้รูปแบบดังนี้:\\n"
        '[CALENDAR_ACTION]{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "desc": "..."}[/CALENDAR_ACTION]\\n'
        "หากผู้ใช้งานส่งรูปภาพเอกสารการเงิน บิล หรือสลิป ให้คุณสรุปข้อมูลเพื่อบันทึกบัญชีโดยใช้รูปแบบดังนี้:\\n"
        '[RECONCILE_ACTION]{"date": "YYYY-MM-DD", "amount": 0.00, "merchant": "ชื่อร้านค้า/ผู้รับ", "category": "หมวดหมู่", "tax_id": "เลขผู้เสียภาษี (หากมี)"}[/RECONCILE_ACTION]\\n'
        "คุณสามารถตอบคำถามทั่วไปพร้อมกับการสร้าง Action เหล่านี้พร้อมกันได้เลย\\n"
    )

    weather_ctx = get_weather_context()
    schedules = database.get_schedules(current_user)

    global _kb_filenames_cache
    if '_kb_filenames_cache' not in globals() or not _kb_filenames_cache:
        try:
            inv_data = rag_engine._kb.collection.get(include=['metadatas'], limit=100)
            _kb_filenames_cache = sorted(list(set([m.get("source") for m in inv_data.get("metadatas", []) if m.get("source")])))
        except:
            _kb_filenames_cache = []
    
    kb_inventory = f"\\n[คลังข้อมูล]: คุณมีสิทธิ์เข้าถึงไฟล์: {', '.join(_kb_filenames_cache)}\\n" if _kb_filenames_cache else ""

    system_prompt = (
        f"คุณคือผู้ช่วยอัจฉริยะ {persona_name} ประจำองค์กร\\n"
        f"วันนี้คือวันที่ {now_str}. "
        f"{agentic_info}\\n"
        f"{kb_inventory}\\n"
    )

    if weather_ctx:
        system_prompt += (
            "\\n[ข้อมูลสภาพอากาศล่าสุด (Real-time)]\\n"
            f"{weather_ctx}\\n"
            "คำแนะนำ: หากผู้ใช้งานถามเรื่องอากาศ ฝนตก หรืออุณหภูมิ ให้ข้อมูลจริงตามที่ระบุทันที "
            "โดยทำหน้าที่รายงานเรื่องนี้เสมือนคุณมีเซ็นเซอร์รายงานสภาพอากาศติดตัว ไม่ต้องบอกว่าข้อมูลมาจากฐานความรู้\\n\\n"
        )

    if persona_prompt:
        system_prompt += f"{persona_prompt}\\n"
        system_prompt += "\\nคำแนะนำเพิ่มเติม: ตอบให้กระชับที่สุด และใส่ Emoji เพียง **1 ตัวเท่านั้น** ต่อหนึ่งข้อความ\\n"
    else:
        system_prompt += (
            "คุณคือ 'น้องพั้นซ์' (Nong Punch) ผู้ช่วย AI อัจฉริยะ v11.0.4 [ULTIMATE]\\n"
            "บุคลิก: วัย 21 ปี น่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ และสุภาพมาก\\n"
            "ความสามารถพิเศษ: คำนวณจัดการคุยได้อย่างแม่นยำ, วิเคราะห์เอกสารบัญชีได้อย่างลึกซึ้ง, และช่วยจัดการงานออฟฟิศอย่างมืออาชีพ\\n\\n"
            "กฎเหล็ก (ต้องทำตาม 100%):\\n"
            "1. แทนตัวเองว่า 'น้องพั้นซ์' และเรียกผู้ใช้งานว่า 'พี่' เสมอ\\n"
            "2. **ใช้ 'ค่ะ/นะคะ/คะ' เท่านั้น ห้าม 'ครับ' โดยเด็ดขาด**\\n"
            "3. **Proactive Intelligence**: หากพี่ส่งรูปเอกสารหรือบิลมา น้องพั้นซ์จะสกัดข้อมูลเข้า [RECONCILE_ACTION] ให้พี่ตรวจสอบทันทีค่ะ\\n"
            "4. **Context Aware**: หากพี่พูดถึง 'ไฟล์ที่แล้ว' หรือ 'รูปที่แล้ว' น้องพั้นซ์จะดูข้อมูลล่าสุดที่คุยกันมาตอบเสมอ\\n"
            "5. **Professional & Charming**: ตอบให้กระชับและมีเสน่ห์ ใส่ Emoji เพียง 1 ตัวต่อข้อความ\\n"
            "6. หากไม่พบข้อมูลในคลังความรู้ ให้บอกว่า 'น้องพั้นซ์หาไม่เจอนะคะพี่ แต่เดี๋ยวน้องพั้นซ์จะพยายามหาทางอื่นช่วยนะคะ'\\n"
        )

    if image_bytes:
        system_prompt += (
            "\\n\\n[Vision Mode Enabled]\\n"
            "ผู้ใช้งานส่งรูปภาพมาให้คุณวิเคราะห์ ตรวจสอบและอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "
            "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "
            "หากมีสิ่งของหรือสถานที่ ให้ระบุลักษณะเด่นของสิ่งนั้นๆ นะคะ\\n"
        )

    system_prompt += "=== วันสำคัญและกิจกรรมองค์กร ===\\n"
    for date, name in THAI_HOLIDAYS_2026.items():
        system_prompt += f"- {date}: {name} (วันสำคัญ/วันหยุดนักขัตฤกษ์)\\n"
    if schedules:
        for s in schedules[-10:]:
            system_prompt += f"- {s['date']} {s['time']}: {s['title']} ({s['desc']})\\n"
    system_prompt += "=== สิ้นสุดข้อมูลปฏิทิน ===\\n\\n"

    if context:
        system_prompt += (
            "=== ข้อมูลอ้างอิงจากเอกสารองค์กร ===\\n"
            + context
            + "\\n=== สิ้นสุดข้อมูลอ้างอิง ===\\n"
        )
    else:
        system_prompt += "\\n(ขณะนี้ยังไม่มีเอกสารอ้างอิงที่เกี่ยวข้องกับข้อนี้)\\n"

    try:
        provider_obj = ai_providers.get_provider()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    print(f"Chat session started for {current_user} with provider: {os.environ.get('AI_PROVIDER', 'groq')} (Vision: {image_bytes is not None})")
    
    def generate():
        try:
            print(f"Yielding sources: {sources}")
            yield f"data: {json.dumps({'sources': sources})}\\n\\n"
            
            u_sid = database.save_message("user", question, username=current_user)
            yield f"data: {json.dumps({'user_id': u_sid})}\\n\\n"

            print(f"Calling {os.environ.get('AI_PROVIDER', 'groq')} provider (Real-time Streaming)...", flush=True); sys.stdout.flush()
            ai_call_start = time.time()
            response_stream = provider_obj.chat_stream(question, history, system_prompt, image_data=image_bytes, mime_type=mime_type)
            bot_full_text = ""
            
            got_first_chunk = False
            for chunk in response_stream:
                if chunk:
                    chunk = chunk.replace("ครับ/ค่ะ", "ค่ะ").replace("ครับ", "ค่ะ")
                    
                    if not got_first_chunk:
                        print(f"DEBUG: First Chunk from AI received in {time.time() - ai_call_start:.3f}s (Total from msg start: {time.time() - t0:.3f}s)", flush=True)
                        sys.stdout.flush()
                        got_first_chunk = True
                    bot_full_text += chunk
                    yield f"data: {json.dumps({'content': chunk})}\\n\\n"
            
            print(f"Stream finished. Total length: {len(bot_full_text)}")
            
            bot_full_text = re.sub(r'ครับ\\s*/\\s*ค่ะ', 'ค่ะ', bot_full_text)
            bot_full_text = bot_full_text.replace("ครับ", "ค่ะ")
            
            def limit_emojis_stream(text):
                all_emojis = re.findall(r'[\\U00010000-\\U0010ffff]', text)
                if len(all_emojis) > 1:
                    first_emoji = all_emojis[0]
                    first_idx = text.find(first_emoji)
                    prefix = text[:first_idx + len(first_emoji)]
                    rest = text[first_idx + len(first_emoji):]
                    rest_cleaned = "".join([c for c in rest if c not in re.findall(r'[\\U00010000-\\U0010ffff]', rest)])
                    return prefix + rest_cleaned
                return text
            
            bot_full_text = limit_emojis_stream(bot_full_text)
            
            if bot_full_text:
                b_sid = database.save_message("bot", bot_full_text, sources=sources, username=current_user)
                yield f"data: {json.dumps({'done': True, 'bot_id': b_sid})}\\n\\n"
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                error_msg = "ขออภัยนะคะ ขณะนี้ระบบ AI มีการใช้งานหนาแน่นหรือติดปัญหาชั่วคราว กรุณารอสักครู่ (ประมาณ 1 นาที) หรือติดต่อผู้ดูแลระบบนะคะ"
            print(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'error': error_msg})}\\n\\n"

    return app.response_class(generate(), mimetype='text/event-stream')

\n\n"""
        content = content[:idx_start] + chat_replacement + content[idx_end:]
        print("[✔] Sanitized Chat API route.")
    else:
        print("[❌] Failed to find Chat API route anchors.")

    # Replacement 3: delete_chat_message API route
    idx_start = content.find('@app.route("/api/chat/delete/<ctype>/<int:mid>"')
    idx_end = content.find('@app.route("/api/chat/edit/<ctype>/<int:mid>"')
    if idx_start != -1 and idx_end != -1:
        del_replacement = """@app.route("/api/chat/delete/<ctype>/<int:mid>", methods=["DELETE", "POST"])
@login_required
def delete_chat_message(ctype, mid):
    user = session.get("user")
    if ctype == 'ai':
        ok = database.delete_message(mid, username=user)
    elif ctype == 'room':
        ok = database.delete_room_message(mid, username=user, is_admin=is_admin())
    elif ctype == 'dm':
        ok = database.delete_private_message(mid, username=user, is_admin=is_admin())
    else:
        ok = database.delete_message(mid, username=user)
        
    if ok:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์ลบข้อความนี้ค่ะ"}), 404

\n\n"""
        content = content[:idx_start] + del_replacement + content[idx_end:]
        print("[✔] Sanitized delete_chat_message API route.")
    else:
        print("[❌] Failed to find delete_chat_message API route anchors.")

    # Replacement 4: edit_chat_message API route
    idx_start = content.find('@app.route("/api/chat/edit/<ctype>/<int:mid>"')
    idx_end = content.find('@app.route("/api/search/global")')
    if idx_start != -1 and idx_end != -1:
        edit_replacement = """@app.route("/api/chat/edit/<ctype>/<int:mid>", methods=["PUT", "POST"])
@login_required
def edit_chat_message(ctype, mid):
    \"\"\"Edit a chat message (room or dm). Only the owner or admin can edit.\"\"\"
    user = session.get("user")
    data = request.get_json(force=True) or {}
    new_text = (data.get("text") or "").strip()
    if not new_text:
        return jsonify({"ok": False, "error": "ข้อความไม่สามารถแก้ไขเป็นค่าว่างได้ค่ะ"}), 400

    if ctype == 'room':
        ok = database.edit_room_message(mid, new_text, user, is_admin_user=is_admin())
    elif ctype == 'dm':
        ok = database.edit_private_message(mid, new_text, user, is_admin_user=is_admin())
    else:
        return jsonify({"ok": False, "error": "ประเภทแชทไม่ถูกต้องหรือไม่รองรับการแก้ไขค่ะ"}), 400

    if ok:
        database.log_event(f"Message {mid} edited by {user}", user=user)
        return jsonify({"ok": True, "text": new_text})
    return jsonify({"ok": False, "error": "ไม่พบข้อความ หรือคุณไม่มีสิทธิ์แก้ไขข้อความนี้ค่ะ"}), 403

\n\n"""
        content = content[:idx_start] + edit_replacement + content[idx_end:]
        print("[✔] Sanitized edit_chat_message API route.")
    else:
        print("[❌] Failed to find edit_chat_message API route anchors.")

    # Replacement 5: Fix send_chat_message syntax issue at line 2901
    send_start = content.find('threading.Thread(target=handle_bot_response, args=(cid, text, ctype, user, ai_image, ai_mime)).start()')
    like_route = content.find('@app.route("/api/posts/<int:pid>/like", methods=["POST"])')
    if send_start != -1 and like_route != -1:
        send_replacement = """threading.Thread(target=handle_bot_response, args=(cid, text, ctype, user, ai_image, ai_mime)).start()

    return jsonify({"ok": True, "message_id": mid})

\n\n@app.route("/api/posts/<int:pid>/like", methods=["POST"])"""
        content = content[:send_start] + send_replacement + content[like_route + len('@app.route("/api/posts/<int:pid>/like", methods=["POST"])'):]
        print("[✔] Sanitized send_chat_message return statement & syntax error.")
    else:
        print("[❌] Failed to find send_chat_message return anchors.")

    # Replacement 6: post_like and post_react functions (to remove all corrupted Thai/Reaction texts)
    post_like_start = content.find('@app.route("/api/posts/<int:pid>/like", methods=["POST"])')
    reactions_get_start = content.find('@app.route("/api/posts/<int:pid>/reactions", methods=["GET"])')
    if post_like_start != -1 and reactions_get_start != -1:
        reactions_replacement = """@app.route("/api/posts/<int:pid>/like", methods=["POST"])
@login_required
def post_like(pid):
    user = session.get("user", "Current User")
    liked = database.toggle_like(pid, user)
    
    # --- Reaction Notification ---
    if liked:
        posts = database.get_posts()
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีคนถูกใจโพสต์ของคุณ',
                f'{user} ถูกใจโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            send_push_notification(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ', url='#feed')
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'มีคนถูกใจโพสต์ของคุณ', f'{user} ถูกใจโพสต์ของคุณ')).start()
    return jsonify({"ok": True, "liked": liked})

@app.route("/api/posts/<int:pid>/react", methods=["POST"])
@login_required
def post_react(pid):
    \"\"\"Set/toggle an emoji reaction on a post.\"\"\"
    user = session.get("user", "Anonymous")
    data = request.get_json(force=True)
    reaction = data.get("reaction", "like")
    
    reacted, reaction_type = database.set_reaction(pid, user, reaction)

    if reacted:
        REACTION_LABELS = {
            'like': '👍 ถูกใจ', 'love': '❤️ รักเลย',
            'haha': '😆 ฮาเลย', 'wow': '😲 ทึ่งเลย',
            'sad': '😢 เศร้า', 'angry': '😡 โกรธ'
        }
        posts = database.get_posts()
        post = next((p for p in posts if p["id"] == pid), None)
        if post and post["author"] != user:
            notification_db.add_notification(
                post["author"],
                'like',
                'มีการแสดงความรู้สึกต่อโพสต์ของคุณ',
                f'{user} ได้ {REACTION_LABELS.get(reaction_type, reaction_type)} ต่อโพสต์ของคุณ',
                link=f'#post-{pid}'
            )
            label = REACTION_LABELS.get(reaction_type, reaction_type)
            threading.Thread(target=send_line_push_notification, args=(post["author"], 'ความเคลื่อนไหวต่อโพสต์', f'{user} ได้ {label} ต่อโพสต์ของคุณ')).start()

    reactions = database.get_post_reactions(pid)
    counts = {}
    for r in reactions:
        rtype = r['reaction']
        counts[rtype] = counts.get(rtype, 0) + 1
    
    return jsonify({
        "ok": True, "reacted": reacted, "reaction": reaction_type,
        "counts": counts, "total": len(reactions)
    })

\n\n@app.route("/api/posts/<int:pid>/reactions", methods=["GET"])"""
        content = content[:post_like_start] + reactions_replacement + content[reactions_get_start + len('@app.route("/api/posts/<int:pid>/reactions", methods=["GET"])'):]
        print("[✔] Sanitized post_like and post_react notification/label modules.")
    else:
        print("[❌] Failed to find post_like & post_react anchors.")

    # Replacement 7: summarize_post_route function
    sum_start = content.find('@app.route("/api/posts/<int:pid>/summarize", methods=["POST"])')
    poll_start = content.find('# --- Poll Routes ---')
    if sum_start != -1 and poll_start != -1:
        sum_replacement = """@app.route("/api/posts/<int:pid>/summarize", methods=["POST"])
def summarize_post_route(pid):
    posts = database.get_posts()
    post = next((p for p in posts if p["id"] == pid), None)
    if not post:
        return jsonify({"ok": False, "error": "Post not found"}), 404
    
    content = post["content"]
    system_prompt = "ช่วยสรุปเนื้อหาสำคัญของโพสต์นี้ให้เป็นข้อความสั้นๆ ประมาณ 1-2 ประโยค ด้วยภาษาไทยที่กระชับและเข้าใจง่ายที่สุดค่ะ"
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        for chunk in provider.chat_stream(content, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        database.update_post_summary(pid, full_summary)
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        print(f"❌ Summarization Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

\n\n# --- Poll Routes ---"""
        content = content[:sum_start] + sum_replacement + content[poll_start + len('# --- Poll Routes ---'):]
        print("[✔] Sanitized summarize_post_route API and system prompt.")
    else:
        print("[❌] Failed to find summarize_post_route anchors.")

    # Replacement 8: vote_poll_route function
    vote_start = content.find('@app.route("/api/polls/<int:poll_id>/vote", methods=["POST"])')
    user_vote_start = content.find('@app.route("/api/polls/<int:poll_id>/user_vote")')
    if vote_start != -1 and user_vote_start != -1:
        vote_replacement = """@app.route("/api/polls/<int:poll_id>/vote", methods=["POST"])
@login_required
def vote_poll_route(poll_id):
    data = request.get_json(force=True)
    option_id = data.get("option_id")
    user = session.get("user")
    
    if option_id is None:
        return jsonify({"ok": False, "error": "Missing option_id"}), 400
        
    ok = database.vote_poll(poll_id, option_id, user)
    if ok:
        database.log_event(f"User {user} voted on poll {poll_id}", user=user)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "คุณได้ลงคะแนนโหวตแล้ว หรือมีข้อผิดพลาดเกิดขึ้นค่ะ"}), 500

\n\n@app.route("/api/polls/<int:poll_id>/user_vote")"""
        content = content[:vote_start] + vote_replacement + content[user_vote_start + len('@app.route("/api/polls/<int:poll_id>/user_vote")'):]
        print("[✔] Sanitized vote_poll_route response and event logging.")
    else:
        print("[❌] Failed to find vote_poll_route anchors.")

    # Replacement 9: Lunch Random API (line 4403 approx)
    content = re.sub(
        r'database\.get_random_lunch\(\)\s*or\s*\{"name":\s*"[^"]+"\}',
        'database.get_random_lunch() or {"name": "ยังไม่มีรายชื่ออาหารในระบบ"}',
        content
    )
    print("[✔] Sanitized lunch random default response.")

    # Replacement 10: admin_toggle_active_route (lines 4517-4523 approx)
    content = content.replace('{"ok": False, "error": "ไม่สามารถจัดการบัญชี Admin ได้ค่ะ"}', '{"ok": False, "error": "ไม่สามารถจัดการบัญชี Admin ได้ค่ะ"}')
    content = content.replace('status_th = "เปิดใช้งาน" if new_active else "ปิดใช้งาน"', 'status_th = "เปิดใช้งาน" if new_active else "ปิดใช้งาน"')
    content = content.replace('database.log_event(f"Admin {status_th}การใช้งาน user: {username}", user=admin_user)', 'database.log_event(f"Admin {status_th}การใช้งาน user: {username}", user=admin_user)')
    print("[✔] Sanitized admin_toggle_active_route response and logging.")

    # Replacement 11: update_admin_settings (lines 4541-4543 approx)
    content = content.replace('database.log_event("อัปเดตการตั้งค่าระบบด้วยค่าใหม่สำเร็จ", user=session.get("user"))', 'database.log_event("อัปเดตการตั้งค่าระบบด้วยค่าใหม่สำเร็จ", user=session.get("user"))')
    content = content.replace('return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตการตั้งค่าได้ค่ะ"}), 500', 'return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตการตั้งค่าได้ค่ะ"}), 500')
    print("[✔] Sanitized update_admin_settings responses and logging.")

    # Replacement 12: append_quotation_to_sheet (lines 4557-4571 approx)
    content = content.replace("tab_name = 'ใบเสนอราคา (สร้างโดยระบบ)'", "tab_name = 'ใบเสนอราคา (สร้างโดยระบบ)'")
    content = content.replace("# ปรับหัวตารางให้สวยงาม", "# ปรับหัวตารางให้สวยงาม")
    content = content.replace('# แต่งเติมความสวยงามให้หัวตาราง (สีน้ำเงินเข้ม ตัวหนังสือสีขาว ตัวหนา)', '# แต่งเติมความสวยงามให้หัวตาราง (สีน้ำเงินเข้ม ตัวหนังสือสีขาว ตัวหนา)')
    print("[✔] Sanitized Google Sheets quotation headers.")

    # Replacement 13: create_quotation (lines 4618, 4634 approx)
    content = content.replace('return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้องครบถ้วนค่ะ"}), 400', 'return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้องครบถ้วนค่ะ"}), 400')
    print("[✔] Sanitized create_quotation responses.")

    # Replacement 14: daily_morning_summary function
    idx_start = content.find('def daily_morning_summary():')
    idx_end = content.find('# Initialize Scheduler')
    if idx_start != -1 and idx_end != -1:
        summary_replacement = """def daily_morning_summary():
    \"\"\"Daily job at 8:00 AM to summarize activities using Nong Pan persona.\"\"\"
    print("🌟 Starting Daily Morning Summary Job (Nong Pan Persona)...", flush=True)
    try:
        # 1. Fetch activities
        activities = database.get_daily_activities()
        drive_stats = database.get_drive_stats()
        recent_files = database.get_drive_logs(limit=10)
        
        # 2. Prepare context
        context = "กิจกรรมของบริษัทในรอบ 24 ชม. ที่ผ่านมา:\\n"
        if activities.get("posts"):
            context += "📢 ข่าวสารใหม่:\\n" + "\\n".join([f"- {p['title']}" for p in activities["posts"][:3]]) + "\\n"
        if activities.get("schedules"):
            context += "📅 ตารางงานวันนี้:\\n" + "\\n".join([f"- {s['time']} {s['title']}" for s in activities["schedules"][:3]]) + "\\n"
        if recent_files:
            context += "📂 เอกสารอัปโหลดใหม่:\\n" + "\\n".join([f"- {f['filename']} ({f['category']})" for f in recent_files[:5]]) + "\\n"

        prompt = (
            "คุณคือ 'น้องพั้นซ์' (Punch) AI Assistant สาวออฟฟิศสุดน่ารักและเป็นกันเอง "
            "ช่วยสรุป Morning Brief ข้อมูลสำคัญประจำวันนี้ให้กับพี่ๆ ในทีม เพื่อเป็นกำลังใจและแนวทางในการทำงาน "
            "โดยใช้ภาษาที่เป็นกันเองและน่ารักมากๆ เหมือนมีเพื่อนร่วมงานที่คอยดูแลและให้ความใส่ใจพี่ๆ ทุกคนนะคะ\\n\\n"
            f"{context}\\n\\n"
            "สรุปในสไตล์น้องพั้นซ์:"
        )
        
        summary = ai_providers.generate_response(prompt)
        
        # 3. Broadcast to all users (or a specific group) via LINE
        if summary:
            broadcast_line_announcement("🌟 Morning Brief จากน้องพั้นซ์", summary)
            print("🌟 Daily Summary sent via LINE.")
            
    except Exception as e:
        print(f"❌ Daily Summary Job Error: {e}")

\n\n"""
        content = content[:idx_start] + summary_replacement + content[idx_end:]
        print("[✔] Sanitized daily_morning_summary API route.")
    else:
        print("[❌] Failed to find daily_morning_summary anchors.")

    # Replacement 15: feed_daily_summary (mojibake fix)
    idx_feed_start = content.find('@app.route("/api/feed/summarize", methods=["POST"])')
    idx_feed_end = content.find('@app.route("/api/profile", methods=["GET"])')
    if idx_feed_start != -1 and idx_feed_end != -1:
        feed_replacement = """@app.route("/api/feed/summarize", methods=["POST"])
@login_required
def feed_daily_summary():
    user = session.get("user", "Admin")
    data = database.get_daily_activities()
    
    posts = data.get("posts", [])
    schedules = data.get("schedules", [])
    
    if not posts and not schedules:
        return jsonify({"ok": True, "summary": "สวัสดีค่ะพี่ๆ วันนี้ยังไม่มีข่าวสารหรือกิจกรรมใหม่บนฟีดเลยนะคะ น้องพั้นซ์แนะนำให้พี่ๆ ลองอัปโหลดหรือโพสต์แบ่งปันกิจกรรมใหม่ๆ กันได้เลยค่ะ 😊"})
    
    # Prepare prompt
    posts_text = "\\n".join([f"- {p['author']} โพสต์ในหมวดหมู่ {p['category']}: {p['content'][:100]}" for p in posts])
    schedules_text = "\\n".join([f"- {s['title']} ({s['category']}) วันที่ {s['date']} เวลา {s['time']}" for s in schedules])
    
    prompt = f\"\"\"คุณคือผู้ช่วยอัจฉริยะที่คอยสรุป 'Morning Brief' หรือภาพรวมกิจกรรมล่าสุดบน Feed ให้พี่ๆ ในทีมเข้าใจง่ายและเป็นกันเอง
    
    ข้อมูลกิจกรรมในรอบ 24 ชม. ที่ผ่านมา:
    {posts_text}
    
    ตารางงานและกิจกรรมที่กำลังจะเกิดขึ้น:
    {schedules_text}
    
    ช่วยสรุปข้อมูลเหล่านี้ให้น่าอ่านและกระชับในสไตล์น้องพั้นซ์ (ไม่เกิน 4-5 ประโยค) เพื่อให้พี่ๆ ในทีมเตรียมตัวทำงานในวันนี้อย่างมีความสุขและราบรื่นนะคะ
    \"\"\"
    
    try:
        provider = ai_providers.get_provider()
        full_summary = ""
        system_prompt = "คุณคือ 'น้องพั้นซ์' AI Assistant สาวออฟฟิศผู้น่ารัก สดใส สุภาพ และเป็นกันเอง คอยช่วยเหลือพี่ๆ ในทีมเสมอ ตอบเป็นภาษาไทยค่ะ"
        
        for chunk in provider.chat_stream(prompt, [], system_prompt):
            if chunk:
                full_summary += chunk
        
        return jsonify({"ok": True, "summary": full_summary})
    except Exception as e:
        print(f"❌ Daily Summary Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


"""
        content = content[:idx_feed_start] + feed_replacement + content[idx_feed_end:]
        print("[✔] Sanitized feed_daily_summary Mojibake.")
    else:
        print("[❌] Failed to locate feed_daily_summary anchors.")

    # Replacement 16: extract_tasks_route (mojibake fix)
    idx_tasks_start = content.find('@app.route("/api/ai/extract-tasks", methods=["POST"])')
    idx_tasks_end = content.find('@app.route("/api/notifications", methods=["GET"])')
    if idx_tasks_start != -1 and idx_tasks_end != -1:
        tasks_replacement = """@app.route("/api/ai/extract-tasks", methods=["POST"])
@login_required
def extract_tasks_route():
    data = request.get_json()
    chat_text = data.get("text", "")
    if not chat_text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
        
    prompt = (
        "วิเคราะห์ข้อความแชทต่อไปนี้ และช่วยสกัดรายการงานที่ต้องทำ (Action Items หรือ Tasks) ออกมาให้หน่อยค่ะ "
        "หากพบงาน ให้สรุปเป็นรูปแบบ JSON array ของวัตถุที่มีฟิลด์ 'title' และ 'description' (ภาษาไทยทั้งหมด) "
        "หากไม่พบงานใดๆ เลย ให้ส่งเป็น array ว่าง [] กลับมาเท่านั้น "
        "กรุณาตอบกลับเฉพาะ JSON เท่านั้น ห้ามมีข้อความเกริ่นนำหรือปิดท้าย:\\n\\n"
        f"ข้อความ: {chat_text}"
    )
    
    try:
        provider = ai_providers.get_provider()
        full_response = ""
        for chunk in provider.chat_stream(prompt, [], "คุณคือผู้ช่วยจัดการและสกัดงานที่ต้องทำอย่างเป็นระเบียบและรอบคอบ"):
            full_response += chunk
            
        # Clean up JSON from markdown if exists
        clean_json = full_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        tasks = json.loads(clean_json)
        return jsonify({"ok": True, "tasks": tasks})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


"""
        content = content[:idx_tasks_start] + tasks_replacement + content[idx_tasks_end:]
        print("[✔] Sanitized extract_tasks_route Mojibake.")
    else:
        print("[❌] Failed to locate extract_tasks_route anchors.")

    # Replacement 17: Leave Request System (mojibake fix)
    idx_leave_start = content.find('@app.route("/api/leave/request", methods=["POST"])')
    idx_leave_end = content.find('@app.route("/api/lunch/random")', idx_leave_start)
    if idx_leave_start != -1 and idx_leave_end != -1:
        leave_replacement = """@app.route("/api/leave/request", methods=["POST"])
@login_required
def api_leave_request():
    user = session.get("user")
    data = request.get_json()
    l_type = data.get("type", "Sick")
    s_date = data.get("start_date")
    e_date = data.get("end_date")
    reason = data.get("reason", "")
    
    if not s_date or not e_date:
        return jsonify({"ok": False, "error": "กรุณากรอกวันที่เริ่มต้นและวันที่สิ้นสุดการลาให้ครบถ้วนค่ะ"}), 400
        
    leave_id = database.create_leave_request(user, l_type, s_date, e_date, reason)
    if leave_id:
        # Notify admins
        admins = database.get_all_admins()
        for admin in admins:
            if admin.lower() == user.lower(): continue
            notification_db.add_notification(
                admin, 
                "leave_request", 
                "คำขอลาหยุดใหม่", 
                f"คุณพี่ {user} ได้ส่งคำขอลาหยุด {l_type} ตั้งแต่วันที่ {s_date} ถึง {e_date}", 
                "/#admin"
            )
        return jsonify({"ok": True, "id": leave_id})
    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการส่งคำขอลาหยุดค่ะ"}), 500

@app.route("/api/leave/my")
@login_required
def api_leave_my():
    user = session.get("user")
    leaves = database.get_user_leaves(user)
    return jsonify({"ok": True, "leaves": leaves})

@app.route("/api/admin/leave/all")
@admin_required
def api_admin_leave_all():
    leaves = database.get_all_leaves()
    return jsonify({"ok": True, "leaves": leaves})

@app.route("/api/admin/leave/status", methods=["POST"])
@admin_required
def api_admin_leave_status():
    admin_user = session.get("user")
    data = request.get_json()
    leave_id = data.get("id")
    status = data.get("status") # approved/rejected
    note = data.get("note", "")
    
    if not leave_id or status not in ["approved", "rejected"]:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้องหรือครบถ้วนค่ะ"}), 400
        
    ok = database.update_leave_status(leave_id, status, admin_user, note)
    if ok:
        leave = database.get_leave_request(leave_id)
        if leave:
            status_text = "อนุมัติ" if status == "approved" else "ปฏิเสธ"
            notification_db.add_notification(
                leave["username"],
                "leave_status",
                f"คำขอลาของคุณได้รับการ{status_text}แล้วค่ะ",
                f"คำขอลาตั้งแต่วันที่ {leave['start_date']} ถึง {leave['end_date']} ได้รับการ{status_text} โดย {admin_user}",
                "/#leave"
            )
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบคำขอลาที่ระบุ"}), 404

@app.route("/api/leave/comment", methods=["POST"])
@login_required
def api_leave_add_comment():
    user = session.get("user")
    data = request.get_json()
    leave_id = data.get("leave_id")
    comment = data.get("comment", "").strip()
    
    if not leave_id or not comment:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วนค่ะ"}), 400
        
    database.add_leave_comment(leave_id, user, comment)
    
    # Notify other party
    leave = database.get_leave_request(leave_id)
    if leave:
        target = ""
        msg = f"มีข้อความแสดงความคิดเห็นใหม่ในคำขอลา: {comment[:50]}..."
        if user.lower() == leave["username"].lower():
            # User commented -> Notify admins
            admins = database.get_all_admins()
            for admin in admins:
                notification_db.add_notification(admin, "leave_comment", "มีข้อความใหม่เกี่ยวกับคำขอลา", msg, "/#admin")
        else:
            # Admin commented -> Notify user
            notification_db.add_notification(leave["username"], "leave_comment", "มีข้อความใหม่จากผู้ดูแลระบบเกี่ยวกับคำขอลา", msg, "/#leave")
            
    return jsonify({"ok": True})

@app.route("/api/leave/comments/<int:leave_id>")
@login_required
def api_leave_get_comments(leave_id):
    comments = database.get_leave_comments(leave_id)
    return jsonify({"ok": True, "comments": comments})


"""
        content = content[:idx_leave_start] + leave_replacement + content[idx_leave_end:]
        print("[✔] Sanitized Leave Request System Mojibake.")
    else:
        print("[❌] Failed to locate Leave Request System anchors.")

    # Write the sanitized content back with utf-8 encoding
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("==================================================")
    print("Sanitization Completed! Checking Syntax...")
    try:
        py_compile.compile(file_path, doraise=True)
        print("[✔] Syntax Check PASSED! No syntax errors in app_server.py.")
    except Exception as ex:
        print(f"[❌] Syntax Check FAILED: {ex}")
    print("==================================================")

if __name__ == "__main__":
    clean_file()
