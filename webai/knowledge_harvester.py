import os
import json
import logging
import sqlite3
from pathlib import Path

# Try to import Gemini/AI provider if available
try:
    from .ai_providers import ask_gemini_vision
except ImportError:
    ask_gemini_vision = None

logger = logging.getLogger(__name__)

class KnowledgeHarvester:
    """
    Analyzes chat messages to identify recurring questions or valuable info
    and proposes Wiki/Knowledge Base entries.
    """
    
    @staticmethod
    def analyze_recent_messages(org_id=1, limit=500):
        """
        Fetches recent group messages and uses AI to identify knowledge gaps.
        """
        from .database import _get_conn
        from .ai_providers import generate_response

        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get messages from the last 7 days
        cursor.execute("""
            SELECT username, text, timestamp 
            FROM group_messages 
            WHERE organization_id = ? AND timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC LIMIT ?
        """, (org_id, limit))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        messages_text = "\n".join([f"{r['username']}: {r['text']}" for r in rows if r['text']])

        prompt = f"""
        You are a Knowledge Manager. Analyze these chat logs from a company LINE group and identify 3 recurring questions or important internal procedures mentioned.
        For each, create a Title and a concise Article Content (in Thai).

        Format your response EXCLUSIVELY as a valid JSON list of objects:
        [
          {{"title": "หัวข้อคู่มือ", "content": "เนื้อหาคู่มือแบบละเอียดแต่กระชับ", "reason": "ทำไมถึงเลือกหัวข้อนี้"}}
        ]

        Chat Logs:
        {messages_text}
        """

        try:
            response = generate_response(prompt, system_prompt="You are an expert at distilling unstructured chat into professional company wiki articles. Output ONLY JSON.")
            # Clean JSON if AI adds markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            drafts = json.loads(response)

            created_ids = []
            for d in drafts:
                # Add reason to the content for transparency
                content_with_reason = f"{d['content']}\n\n---\n*เหตุผลที่ AI แนะนำ: {d['reason']}*"
                wiki_id = KnowledgeHarvester.create_wiki_draft(d['title'], content_with_reason, org_id=org_id)
                if wiki_id:
                    created_ids.append(wiki_id)

            return created_ids
        except Exception as e:
            logger.error(f"Error in knowledge harvesting AI: {e}")
            return None


    @staticmethod
    def create_wiki_draft(title, content, author="AI Assistant", org_id=1):
        """
        Inserts a draft article into the wiki system.
        """
        from .database import _get_conn
        conn = _get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO wiki_pages (title, content, author, organization_id, status)
                VALUES (?, ?, ?, ?, 'draft')
            """, (title, content, author, org_id))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating wiki draft: {e}")
            return None
        finally:
            conn.close()
