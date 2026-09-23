# -*- coding: utf-8 -*-
"""
Autonomous Browser Agent for OrgChat AI
Provides secure, sandboxed headless web exploration, automated scraping, search, and page screenshot capture.
Built with SSRF protection, private IP filtering, and resource guards.
"""

import os
import re
import io
import time
import base64
import logging
import ipaddress
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("OrgChatAI.BrowserAgent")

# ─── SSRF & Safe Host Protection ─────────────────────────────────────────────
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"}


def is_safe_url(url: str) -> tuple[bool, str]:
    """Validates that a URL uses http(s) and does not point to private/internal networks."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname"

        if hostname.lower() in BLOCKED_HOSTNAMES:
            return False, f"Access to host '{hostname}' is blocked for security."

        # Check IP if hostname is an IP address
        try:
            ip_obj = ipaddress.ip_address(hostname)
            for net in BLOCKED_IP_RANGES:
                if ip_obj in net:
                    return False, f"Access to private IP range {net} is blocked."
        except ValueError:
            # It's a regular domain name
            pass

        return True, "Safe"
    except Exception as e:
        return False, str(e)


class BrowserAgent:
    """Manages browser sessions, live web navigation, and data extraction."""

    def __init__(self):
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OrgChatAI-BrowserAgent/1.0"
        )

    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fast web search fallback using DuckDuckGo HTML without external API keys."""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            res = requests.post(url, data=data, headers=headers, timeout=8)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            results = []

            for el in soup.find_all("div", class_="result", limit=max_results):
                title_el = el.find("a", class_="result__a")
                snippet_el = el.find("a", class_="result__snippet")
                if title_el:
                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    
                    # Extract actual target link from DuckDuckGo redirect
                    if "uddg=" in href:
                        parsed_uddg = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "uddg" in parsed_uddg:
                            href = parsed_uddg["uddg"][0]

                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })

            return results
        except Exception as e:
            logger.error(f"[BrowserAgent Search Error] {e}")
            return []

    def browse_page(self, url: str, capture_screenshot: bool = True) -> Dict[str, Any]:
        """
        Navigates to a webpage using Selenium Headless Chrome.
        Extracts title, clean text summary, and an optional Base64 screenshot thumbnail.
        """
        safe, reason = is_safe_url(url)
        if not safe:
            return {"ok": False, "error": f"Security Block: {reason}", "url": url}

        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"user-agent={self.user_agent}")
            options.add_argument("--window-size=1280,800")
            options.page_load_strategy = "eager"

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(15)

            logger.info(f"🌐 [BrowserAgent] Navigating to: {url}")
            driver.get(url)
            time.sleep(1.5)  # Allow initial scripts/renders to settle

            title = driver.title or ""
            html = driver.page_source

            # Extract clean readable text with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "svg", "noscript"]):
                tag.decompose()

            raw_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)[:4000]  # Cap length for LLM context

            screenshot_b64 = None
            if capture_screenshot:
                try:
                    png_bytes = driver.get_screenshot_as_png()
                    screenshot_b64 = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
                except Exception as sc_err:
                    logger.warning(f"[BrowserAgent Screenshot Warning] {sc_err}")

            return {
                "ok": True,
                "title": title,
                "url": driver.current_url,
                "text_summary": clean_text,
                "screenshot": screenshot_b64,
            }
        except Exception as e:
            logger.error(f"[BrowserAgent Navigate Error] {url}: {e}")
            # Fallback to fast requests if selenium fails or times out
            return self._browse_page_requests_fallback(url)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _browse_page_requests_fallback(self, url: str) -> Dict[str, Any]:
        """Lightweight fallback using requests when headless browser cannot launch."""
        try:
            safe, reason = is_safe_url(url)
            if not safe:
                return {"ok": False, "error": f"Security Block: {reason}", "url": url}

            res = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=10)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.title.string if soup.title else ""
            for tag in soup(["script", "style", "nav", "footer", "header", "svg", "noscript"]):
                tag.decompose()

            lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
            clean_text = "\n".join(lines)[:4000]

            return {
                "ok": True,
                "title": title,
                "url": url,
                "text_summary": clean_text,
                "screenshot": None,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url}

    def execute_task(self, prompt: str) -> Dict[str, Any]:
        """
        Interprets a user request, browses the web or specific URLs, and synthesizes answers.
        """
        # 1. Detect if specific URLs are mentioned
        urls = re.findall(r'https?://[^\s<>"\']+', prompt)
        
        extracted_pages = []
        if urls:
            for u in urls[:2]:  # Limit to top 2 links per user task
                data = self.browse_page(u, capture_screenshot=True)
                if data.get("ok"):
                    extracted_pages.append(data)
        else:
            # If no URL, perform web search
            clean_query = prompt.replace("น้องพั้น", "").replace("ช่วยหา", "").replace("ค้นหา", "").replace("ท่องเว็บ", "").strip()
            clean_query = clean_query[:80]
            search_results = self.search_duckduckgo(clean_query, max_results=3)
            
            # Browse top search result
            if search_results:
                top_url = search_results[0]["url"]
                page_data = self.browse_page(top_url, capture_screenshot=True)
                if page_data.get("ok"):
                    page_data["search_results"] = search_results
                    extracted_pages.append(page_data)

        return {
            "ok": True,
            "prompt": prompt,
            "pages": extracted_pages,
        }


# Singleton instance
browser_agent = BrowserAgent()
