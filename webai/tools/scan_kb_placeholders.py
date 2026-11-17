# -*- coding: utf-8 -*-
"""
Knowledge Base Placeholder Scanner for OrgChat AI.
Scans knowledge base files (txt, md, csv, json, etc.) to detect unedited placeholder text
(e.g., '02-XXX-XXXX', '[ใส่ที่อยู่]', 'example@domain.com', 'บริษัท ตัวอย่าง')
so administrators can update original source documents with real corporate information.

Guarantees:
- Read-only: Never modifies, deletes, or writes to any document or database.
- Safe to run on production or local files.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

# Common placeholder regex patterns
PLACEHOLDER_RULES = [
    (
        "PHONE_PLACEHOLDER",
        "Phone number placeholder (e.g. 02-XXX-XXXX, 08X-XXX-XXXX)",
        re.compile(r'\b0[0-9]?-?[xX]{3,4}-?[xX]{3,4}\b|\b0[xX]-[0-9xX]+\b|\b\d{2,3}-[xX]{3,4}-[xX]{4}\b', re.IGNORECASE)
    ),
    (
        "EMAIL_PLACEHOLDER",
        "Placeholder / sample email address (e.g. example@domain.com, test@test.com)",
        re.compile(r'\b[a-zA-Z0-9._%+-]+@(?:example|sample|domain|test|company)\.[a-zA-Z]{2,}\b|\b(?:example|sample|test|yourname|your_email)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', re.IGNORECASE)
    ),
    (
        "BRACKET_INSTRUCTION",
        "Template fill-in instruction in brackets (e.g. [ใส่ข้อมูล], [ระบุเบอร์โทร])",
        re.compile(r'\[(?:ใส่|ระบุ|เพิ่ม|กรอก|ชื่อ|ข้อมูล|รายละเอียด)[^\]\n]{0,50}\]|\{(?:ใส่|ระบุ|เพิ่ม|กรอก|ชื่อ|ข้อมูล|รายละเอียด)[^}\n]{0,50}\}', re.UNICODE)
    ),
    (
        "SAMPLE_COMPANY_NAME",
        "Sample company name (e.g. บริษัท ตัวอย่าง, บริษัท ABC)",
        re.compile(r'บริษัท\s*(?:ตัวอย่าง|สมมุติ|สมมติ|ทดสอบ|ABC|XYZ|จำกัด\s*\(ตัวอย่าง\))', re.UNICODE)
    ),
    (
        "SAMPLE_PERSON_NAME",
        "Sample person name (e.g. นาย สมมุติ, นาย ตัวอย่าง)",
        re.compile(r'(?:นาย|นาง|นางสาว)\s*(?:สมมุติ|สมมติ|ตัวอย่าง|ทดสอบ)', re.UNICODE)
    ),
    (
        "DATE_PLACEHOLDER",
        "Sample / unedited date placeholder (e.g. วัน/เดือน/ปี, วว/ดด/ปป)",
        re.compile(r'(?:วว/ดด/ปป|วัน/เดือน/ปี|\bDD/MM/YYYY\b|วว\.ดด\.ปป|\bYYYY-MM-DD\b)', re.UNICODE | re.IGNORECASE)
    ),
]


def scan_file_text(file_path: str, text: str) -> list[dict]:
    """Scan string content for placeholder patterns line by line."""
    findings = []
    lines = text.splitlines()
    for line_idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        if not line_clean:
            continue
        for rule_id, rule_desc, pattern in PLACEHOLDER_RULES:
            for match in pattern.finditer(line):
                findings.append({
                    "file": str(file_path),
                    "line": line_idx,
                    "rule": rule_id,
                    "description": rule_desc,
                    "matched": match.group(0),
                    "snippet": line_clean[:120],
                })
    return findings


def scan_file(file_path: Path) -> list[dict]:
    """Read a text-based file safely and scan for placeholders."""
    if not file_path.is_file():
        return []
    # Skip binary or very large files
    supported_exts = {".txt", ".md", ".csv", ".json", ".text", ".tsv", ".yaml", ".yml", ".html"}
    if file_path.suffix.lower() not in supported_exts:
        return []
    
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return scan_file_text(str(file_path), content)
    except Exception as e:
        sys.stderr.write(f"⚠️ Error reading {file_path}: {e}\n")
        return []


def scan_kb_directory(dir_path: Path) -> tuple[int, list[dict]]:
    """Scan all files inside the specified directory recursively."""
    if not dir_path.exists():
        return 0, []

    all_findings = []
    total_files = 0
    for root, _, files in os.walk(dir_path):
        for f in sorted(files):
            p = Path(root) / f
            supported_exts = {".txt", ".md", ".csv", ".json", ".text", ".tsv", ".yaml", ".yml", ".html"}
            if p.suffix.lower() in supported_exts:
                total_files += 1
                findings = scan_file(p)
                all_findings.extend(findings)

    return total_files, all_findings


def main():
    parser = argparse.ArgumentParser(description="Scan knowledge base files for placeholder text.")
    parser.add_argument("--dir", type=str, help="Directory to scan (defaults to DATA_DIR/uploads or uploads/)")
    parser.add_argument("--file", type=str, help="Single file to scan")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    # Determine target path
    if args.file:
        target = Path(args.file)
        if not target.exists():
            sys.stderr.write(f"Error: File not found: {target}\n")
            sys.exit(1)
        findings = scan_file(target)
        total_files = 1
    else:
        if args.dir:
            scan_dir = Path(args.dir)
        else:
            data_dir = os.environ.get("DATA_DIR")
            if data_dir and (Path(data_dir) / "uploads").exists():
                scan_dir = Path(data_dir) / "uploads"
            elif os.path.exists("uploads"):
                scan_dir = Path("uploads")
            elif os.path.exists("../uploads"):
                scan_dir = Path("../uploads")
            else:
                scan_dir = Path("uploads")
        
        total_files, findings = scan_kb_directory(scan_dir)

    if args.json:
        print(json.dumps({
            "total_files_scanned": total_files,
            "total_placeholders_found": len(findings),
            "findings": findings
        }, ensure_ascii=False, indent=2))
        return

    # Text report
    print("\n" + "=" * 70)
    print("🔍 Knowledge Base Placeholder Scanner Report")
    print("=" * 70)
    print(f"📂 Scanned files: {total_files}")
    print(f"⚠️  Placeholders found: {len(findings)}")
    print("-" * 70)

    if not findings:
        print("✅ No placeholder patterns found in scanned documents.")
    else:
        # Group by file
        grouped = {}
        for item in findings:
            grouped.setdefault(item["file"], []).append(item)

        for f_path, items in grouped.items():
            print(f"\n📄 File: {f_path} ({len(items)} issues)")
            for it in items:
                print(f"   • Line {it['line']} [{it['rule']}]: matched '{it['matched']}'")
                print(f"     Snippet: {it['snippet']}")

    print("\n" + "=" * 70)
    print("💡 Action: Please update the original files to replace placeholders with real data.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
