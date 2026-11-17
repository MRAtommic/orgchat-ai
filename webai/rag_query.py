# -*- coding: utf-8 -*-
"""
RAG Query Rewriting Helper for OrgChat AI.
Handles conversational follow-up questions (e.g. "ทำไมจะไม่มีไปเช็คดู", "แล้วอีเมลล่ะ", "อันนั้นเท่าไหร่")
by expanding search queries with context from recent user turns, ensuring Chroma/vector search
retrieves the relevant documents even when follow-up queries lack standalone keywords.
"""

import re
import logging

logger = logging.getLogger("rag_query")

# Connective words and reference markers in Thai/English that strongly signal a follow-up query
_FOLLOWUP_PREFIXES = (
    "แล้ว", "แล้วถ้า", "แล้วมี", "แล้วของ", "แล้วอัน", "แล้วเรื่อง",
    "ทำไม", "ทำไมจะไม่มี", "ทำไมไม่มี", "ทำไมถึง",
    "แล้วใคร", "ใครเป็น", "แล้วทำไม", "แล้วที่ไหน",
    "อันนั้น", "อันนี้", "สิ่งนั้น", "ข้อนั้น",
    "เช็คดู", "เช็กดู", "ไปดู", "ลองดู", "ตรวจดู",
    "ไหน", "ตรงไหน", "ที่ไหน", "มีไหม", "มีมั้ย", "มีป่าว",
    "เท่าไหร่", "กี่วัน", "ยังไง", "อย่างไร",
    "why", "what about", "how about", "and", "then", "which one", "who is",
)

_FOLLOWUP_SUFFIXES = (
    "ล่ะ", "ละ", "ด้วย", "เหมือนกัน", "นั้น", "นี้", "หละ", "บ้าง",
)


def is_greeting_or_noise(text: str) -> bool:
    """Check if text is purely a greeting, polite particle, addressing words, or conversational acknowledgment."""
    if not text:
        return True
    t_clean = text.strip().lower()
    # Strip common Thai polite particles, addressing terms (พี่, น้อง, ทุกคน), trailing spaces, and emphasis symbols
    t_base = re.sub(r'(?:ครับ|ค่ะ|คะ|นะครับ|นะคะ|นะ|ค้าบ|จ้า|จ้ะ|คับ|ผมนาย|ดิฉัน|ๆ|พี่|น้อง|ทุกคน|ท่าน|ผม|หนู|\s)+$', '', t_clean).strip()
    t_base = re.sub(r'^(?:น้อง|พี่)\s*', '', t_base).strip()
    greetings = {
        "สวัสดี", "หวัดดี", "ฮัลโหล", "ฮาโหล", "มอนิ่ง", "อรุณสวัสดิ์",
        "ดี", "hello", "hi", "hey", "hi there", "hello there", "ok", "โอเค", "ครับ", "ค่ะ", "คะ",
        "ขอบคุณ", "ขอบใจ", "บาย", "ลาก่อน"
    }
    if t_base in greetings or t_clean in greetings:
        return True
    full_greetings = {
        "สวัสดีครับ", "สวัสดีค่ะ", "สวัสดีคับ", "สวัสดีคะ", "สวัสดีจ้า", "สวัสดีค่า", "สวัสดีค้าบ",
        "สวัสดีครับพี่", "สวัสดีค่ะพี่", "สวัสดีพี่ๆ", "สวัสดีทุกคน", "สวัสดีครับผม",
        "หวัดดีครับ", "หวัดดีค่ะ", "หวัดดีคับ", "หวัดดีครับพี่", "ดีครับ", "ดีค่ะ", "ดีคับ", "ดีจ้า", "ดีครับพี่",
        "ขอบคุณครับ", "ขอบคุณค่ะ", "ขอบคุณคับ", "โอเคครับ", "โอเคค่ะ",
    }
    return t_clean in full_greetings


def is_followup_query(question: str) -> bool:
    """
    Determine if a user question is likely a follow-up referring to earlier conversation turns.
    Returns True if:
    - Starts with connective/follow-up words (e.g., 'แล้วอีเมลล่ะ', 'ทำไมจะไม่มี')
    - Ends with reference particles ('...ล่ะ', '...ด้วย') and is relatively short (< 40 chars)
    - Is very short (< 25 chars) and doesn't contain a clear independent subject
    """
    if not question:
        return False

    q_strip = question.strip().lower()
    
    # 1. Direct prefix matches
    for prefix in _FOLLOWUP_PREFIXES:
        if q_strip.startswith(prefix):
            return True

    # 2. Suffix matches on short queries
    if len(q_strip) <= 40:
        for suffix in _FOLLOWUP_SUFFIXES:
            if q_strip.endswith(suffix):
                return True

    # 3. Very short query (< 25 chars) without standalone context
    clean = re.sub(r'[0-9๐-๙\s\W_]', '', q_strip)
    if len(clean) < 15 and not any(k in q_strip for k in ["สวัสดี", "hello", "hi", "ขอบคุณ", "บาย"]):
        return True

    return False


def extract_recent_user_turns(history: list, max_turns: int = 2) -> list[str]:
    """
    Extract the most recent user queries from conversation history.
    Supports formats:
    - [{'role': 'user', 'text': '...'}, ...]
    - [{'role': 'user', 'content': '...'}, ...]
    - [{'sender': 'username', 'text': '...'}, ...]
    - [('user', 'text'), ...]
    """
    if not history or not isinstance(history, list):
        return []

    user_texts = []
    # Traverse backwards to get the most recent turns
    for item in reversed(history):
        text = ""
        role = ""
        if isinstance(item, dict):
            role = item.get("role") or item.get("sender") or ""
            text = item.get("text") or item.get("content") or ""
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            role = str(item[0])
            text = str(item[1])

        # Skip assistant / system turns
        if role.lower() in ("model", "bot", "assistant", "ai-assistant", "system"):
            continue

        text_clean = text.strip()
        if not text_clean:
            continue

        # Skip pure greetings or very short commands
        if is_greeting_or_noise(text_clean):
            continue

        user_texts.append(text_clean)
        if len(user_texts) >= max_turns:
            break

    # Return in chronological order
    user_texts.reverse()
    return user_texts


def build_search_query(question: str, history: list = None, max_len: int = 300) -> str:
    """
    Construct an enriched search query for RAG retrieval.
    If the question is standalone and comprehensive, returns it unchanged.
    If it is a conversational follow-up, appends context from recent user questions.
    
    Guarantees:
    - Never throws an exception
    - Never mutates input arguments
    - Bounded length (<= max_len)
    """
    if not question:
        return ""

    q_clean = question.strip()
    if not history:
        return q_clean[:max_len]

    # Check if query needs expansion
    if not is_followup_query(q_clean):
        return q_clean[:max_len]

    recent_turns = extract_recent_user_turns(history, max_turns=2)
    if not recent_turns:
        return q_clean[:max_len]

    # Combine recent user context with current follow-up question
    # Example: "ขอเบอร์ติดต่อบริษัทหน่อย" + "ทำไมจะไม่มีไปเช็คดู"
    # -> "ขอเบอร์ติดต่อบริษัทหน่อย ทำไมจะไม่มีไปเช็คดู"
    combined_parts = []
    seen = set()

    for t in recent_turns:
        # Don't duplicate if current question already contains previous text
        if t.lower() not in seen and t.lower() not in q_clean.lower():
            combined_parts.append(t)
            seen.add(t.lower())

    if q_clean.lower() not in seen:
        combined_parts.append(q_clean)

    expanded_query = " ".join(combined_parts).strip()
    
    # Cap total length to max_len
    if len(expanded_query) > max_len:
        expanded_query = expanded_query[:max_len].rsplit(" ", 1)[0]

    logger.debug(f"[RAG Query] Expanded query: '{q_clean}' -> '{expanded_query}'")
    return expanded_query

