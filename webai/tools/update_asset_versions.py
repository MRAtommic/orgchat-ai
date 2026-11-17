# -*- coding: utf-8 -*-
"""OrgChat AI — Automated Asset Versioning & Cache Buster Tool (R6)

Calculates content hashes for all static assets referenced in templates/index.html
and static/sw.js, updating ?v=<hash[:8]> automatically so browsers and Service Workers
always receive fresh assets immediately after changes without manual version bumps.

Usage:
    python tools/update_asset_versions.py [--check]
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

WEBAI_DIR = Path(__file__).resolve().parent.parent


def get_file_hash(rel_path: str) -> str:
    """Calculates short SHA256 hex digest (8 chars) of a static file."""
    clean_rel = rel_path.lstrip("/").replace("\\", "/")
    if clean_rel.startswith("static/"):
        file_path = WEBAI_DIR / clean_rel
    else:
        file_path = WEBAI_DIR / "static" / clean_rel

    if not file_path.exists():
        # Fallback to file in static
        alt = WEBAI_DIR / clean_rel
        if alt.exists():
            file_path = alt
        else:
            return ""

    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()[:8]
    except Exception:
        return ""


def update_template_assets(check_only: bool = False) -> tuple[int, int]:
    """Updates ?v=<hash> in templates/index.html."""
    index_path = WEBAI_DIR / "templates" / "index.html"
    if not index_path.exists():
        return 0, 0

    text = index_path.read_text(encoding="utf-8")
    # Matches href="/static/...css?v=..." or src="/static/...js?v=..."
    pattern = re.compile(r'((?:href|src)=["\'](/static/[^"\']+?)\?v=([^"\']+)["\'])')
    matches = pattern.findall(text)

    updated_count = 0
    new_text = text
    for full, asset_path, old_v in matches:
        file_hash = get_file_hash(asset_path)
        if file_hash and file_hash != old_v:
            new_val = f'{full.split("=")[0]}="{asset_path}?v={file_hash}"'
            new_text = new_text.replace(full, new_val)
            updated_count += 1

    if updated_count > 0 and not check_only:
        index_path.write_text(new_text, encoding="utf-8")

    return len(matches), updated_count


def update_sw_cache(check_only: bool = False) -> bool:
    """Updates CACHE_NAME in static/sw.js."""
    sw_path = WEBAI_DIR / "static" / "sw.js"
    if not sw_path.exists():
        return False

    text = sw_path.read_text(encoding="utf-8")
    # Compute combined hash of core js/css files
    combined_hash = hashlib.sha256()
    for f in ["static/style.css", "static/js/core.js", "static/js/chat.js"]:
        p = WEBAI_DIR / f
        if p.exists():
            combined_hash.update(p.read_bytes())
    new_version = f"orgchat-offline-v{combined_hash.hexdigest()[:6]}"

    m = re.search(r"const\s+CACHE_NAME\s*=\s*['\"]([^'\"]+)['\"];", text)
    if m and m.group(1) != new_version:
        if not check_only:
            new_text = text.replace(m.group(0), f"const CACHE_NAME = '{new_version}';")
            sw_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Auto-update asset version query params and SW cache")
    parser.add_argument("--check", action="store_true", help="Check only, do not write files")
    args = parser.parse_args()

    total, updated = update_template_assets(check_only=args.check)
    sw_updated = update_sw_cache(check_only=args.check)

    print("=" * 60)
    print("📦 OrgChat AI Asset Versioning Tool (R6)")
    print(f"📊 Scanned {total} static asset references in index.html")
    if args.check:
        print(f"🔍 Status: {updated} asset(s) and SW cache require version update.")
    else:
        print(f"✅ Updated {updated} asset version query string(s) to exact content hashes.")
        if sw_updated:
            print("✅ Updated static/sw.js CACHE_NAME to reflect latest assets.")
    print("=" * 60)


if __name__ == "__main__":
    main()

