# -*- coding: utf-8 -*-
"""
Smart Web Crawler & URL Ingestion Engine for OrgChat AI
Crawls web pages, extracts clean content/markdown, chunks text, and indexes into ChromaDB RAG Knowledge Base.
"""
import os
import sys
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
import logging
import requests
from bs4 import BeautifulSoup

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

logger = logging.getLogger("OrgChatAI.WebCrawler")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OrgChatAI-Bot/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
}

class WebCrawler:
    def __init__(self, timeout: int = 15, max_pages: int = 5):
        self.timeout = timeout
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def normalize_url(self, url: str) -> str:
        """Ensure URL has scheme and is normalized."""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        parsed = urllib.parse.urlparse(url)
        # Strip trailing slash and fragments
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), path, parsed.params, parsed.query, ''))

    def is_valid_content_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for crawling within same domain."""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.netloc.lower() != base_domain.lower():
                return False
            # Filter out non-html extensions
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.pdf', '.zip', '.exe', '.mp4', '.mp3', '.css', '.js']:
                return False
            # Filter common utility pages
            if any(p in parsed.path.lower() for p in ['/login', '/logout', '/signup', '/cart', '/checkout', '/admin']):
                return False
            return True
        except Exception:
            return False

    def extract_page_content(self, url: str) -> dict:
        """Fetch and extract clean text, title, and metadata from a single web page."""
        url = self.normalize_url(url)
        try:
            res = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            res.raise_for_status()
            
            # Detect encoding
            if res.encoding is None or res.encoding == 'ISO-8859-1':
                res.encoding = res.apparent_encoding or 'utf-8'

            html = res.text
            soup = BeautifulSoup(html, 'html.parser')

            # 1. Extract Title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title['content'].strip()
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
            if not title:
                title = urllib.parse.urlparse(url).netloc

            # 2. Extract Description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description')
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()

            # 3. Clean unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe', 'svg', 'form', 'button']):
                tag.decompose()

            # 4. Extract Main Content / Articles
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|body|post|entry|main', re.I)) or soup.body
            
            if not main_content:
                main_content = soup

            # Convert to structured text
            lines = []
            if title:
                lines.append(f"# {title}\n")
            if description:
                lines.append(f"> {description}\n")
            lines.append(f"**URL แหล่งที่มา:** {url}\n")

            for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'table', 'blockquote']):
                text = element.get_text(separator=' ', strip=True)
                if not text or len(text) < 3:
                    continue
                
                tag_name = element.name.lower()
                if tag_name == 'h1':
                    lines.append(f"\n## {text}\n")
                elif tag_name == 'h2':
                    lines.append(f"\n### {text}\n")
                elif tag_name in ['h3', 'h4', 'h5', 'h6']:
                    lines.append(f"\n#### {text}\n")
                elif tag_name == 'li':
                    lines.append(f"- {text}")
                elif tag_name == 'blockquote':
                    lines.append(f"> {text}\n")
                elif tag_name == 'table':
                    # Simple table extraction
                    table_rows = []
                    for tr in element.find_all('tr'):
                        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                        if cells:
                            table_rows.append(" | ".join(cells))
                    if table_rows:
                        lines.append("\n" + "\n".join(table_rows) + "\n")
                else:
                    lines.append(f"{text}\n")

            clean_text = "\n".join(lines).strip()
            # Remove redundant empty lines
            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

            # 5. Extract internal links for sub-page crawling
            base_domain = urllib.parse.urlparse(url).netloc
            discovered_links = set()
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                abs_url = urllib.parse.urljoin(url, href)
                if self.is_valid_content_url(abs_url, base_domain) and abs_url != url:
                    discovered_links.add(abs_url)

            return {
                "success": True,
                "url": url,
                "title": title,
                "description": description,
                "text": clean_text,
                "word_count": len(clean_text.split()),
                "char_count": len(clean_text),
                "internal_links": list(discovered_links)[:30],
                "crawled_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error extracting URL {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "title": url,
                "text": "",
                "word_count": 0,
                "internal_links": []
            }

    def crawl_site(self, start_url: str, crawl_subpages: bool = False, max_pages: int = 5) -> list[dict]:
        """Crawl website starting from start_url. Returns list of page content dicts."""
        start_url = self.normalize_url(start_url)
        visited = set()
        to_visit = [start_url]
        results = []

        max_limit = min(max_pages, self.max_pages) if crawl_subpages else 1

        while to_visit and len(results) < max_limit:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            page_data = self.extract_page_content(current_url)

            if page_data.get("success") and len(page_data.get("text", "")) > 50:
                results.append(page_data)
                
                # Add discovered internal links if sub-page crawling enabled
                if crawl_subpages:
                    for link in page_data.get("internal_links", []):
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)

            time.sleep(0.5)  # Be polite to web servers

        return results


def ingest_website_url(
    url: str,
    crawl_subpages: bool = False,
    max_pages: int = 5,
    department: str = "General",
    category_id: int = None,
    org_id: int = 1
) -> dict:
    """
    Crawls URL, parses clean text, chunks, embeds into ChromaDB Knowledge Base, and updates meta.json.
    """
    import hashlib
    import rag_engine
    
    crawler = WebCrawler(max_pages=max_pages)
    pages = crawler.crawl_site(url, crawl_subpages=crawl_subpages, max_pages=max_pages)

    if not pages:
        return {
            "success": False,
            "error": "ไม่สามารถดึงข้อมูลจาก URL ที่ระบุได้ หรือหน้าเว็บไม่มีเนื้อหาข้อความ"
        }

    kb = rag_engine._get_kb()
    if not kb.is_key_valid():
        return {
            "success": False,
            "error": "API Key สำหรับ Vector Embedding ยังไม่ได้ตั้งค่า"
        }

    total_chunks = 0
    total_words = 0
    ingested_pages = []

    meta = rag_engine._load_meta()

    for idx, page in enumerate(pages):
        page_url = page["url"]
        page_title = page["title"] or f"Web Page {idx+1}"
        page_text = page["text"]
        
        # Unique deterministic File ID for URL
        url_hash = hashlib.sha256(page_url.encode('utf-8')).hexdigest()[:16]
        file_id = f"web_{url_hash}"

        # 1. Semantic Chunking
        chunks = rag_engine.chunk_text(page_text, chunk_size=800, overlap=150)
        if not chunks:
            continue

        chunk_metas = []
        for c_idx, ch in enumerate(chunks):
            chunk_metas.append({
                "source": page_title,
                "url": page_url,
                "source_type": "web",
                "file_id": file_id,
                "department": department,
                "category_id": str(category_id) if category_id is not None else "",
                "organization_id": org_id,
                "chunk_index": c_idx,
                "total_chunks": len(chunks),
                "timestamp": page["crawled_at"]
            })

        # 2. Add to ChromaDB Vector Store
        try:
            # Delete old chunks if updating existing URL
            kb.delete_by_file_id(file_id)
            kb.add_chunks(chunks, source_name=page_title, file_id=file_id, metadatas=chunk_metas)
            total_chunks += len(chunks)
            total_words += page["word_count"]

            # 3. Update meta.json record
            meta[file_id] = {
                "name": page_title,
                "url": page_url,
                "path": page_url,
                "chunks": len(chunks),
                "size": page["char_count"],
                "type": "web",
                "department": department,
                "category_id": category_id,
                "organization_id": org_id,
                "status": "ready",
                "word_count": page["word_count"],
                "crawled_at": page["crawled_at"],
                "timestamp": datetime.now().isoformat()
            }
            ingested_pages.append({
                "file_id": file_id,
                "url": page_url,
                "title": page_title,
                "chunks": len(chunks),
                "words": page["word_count"]
            })
        except Exception as e:
            logger.error(f"Error ingesting page {page_url}: {e}")

    rag_engine._save_meta(meta)

    return {
        "success": True,
        "main_url": url,
        "pages_crawled": len(ingested_pages),
        "total_chunks": total_chunks,
        "total_words": total_words,
        "pages": ingested_pages
    }
