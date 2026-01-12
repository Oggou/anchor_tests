"""
Batch-convert OpenDocument files in this repo to plain text for GitHub viewing.

Supported:
  - .odt (OpenDocument Text)
  - .ods (OpenDocument Spreadsheet)  [optional; none currently in this folder]

This script is dependency-free: it reads the zipped OpenDocument container and
extracts text from content.xml.

Usage:
  python3 convert_to_text.py
  python3 convert_to_text.py --out text --overwrite
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}


def _read_content_xml(doc_path: Path) -> str:
    # ODT/ODS are ZIP containers with content.xml inside.
    with zipfile.ZipFile(doc_path, "r") as zf:
        with zf.open("content.xml") as f:
            return f.read().decode("utf-8", errors="replace")


def _parse_xml(xml_text: str) -> ET.Element:
    return ET.fromstring(xml_text)


def odt_to_text(doc_path: Path) -> str:
    xml = _read_content_xml(doc_path)
    root = _parse_xml(xml)

    body = root.find("office:body", NS)
    if body is None:
        return ""

    text_body = body.find("office:text", NS)
    if text_body is None:
        return ""

    # Preserve document order by scanning for paragraphs/headings.
    lines: list[str] = []
    for el in text_body.iter():
        tag = el.tag
        if tag in {f"{{{NS['text']}}}p", f"{{{NS['text']}}}h"}:
            s = "".join(el.itertext()).strip()
            if s:
                lines.append(s)

    # De-dupe adjacent identical lines (common with headers/footers or artifacts).
    cleaned: list[str] = []
    prev = None
    for line in lines:
        if line == prev:
            continue
        cleaned.append(line)
        prev = line

    return "\n\n".join(cleaned).strip() + "\n"


def _int_attr(el: ET.Element, qname: str, default: int = 1) -> int:
    try:
        return int(el.attrib.get(qname, default))
    except Exception:
        return default


def ods_to_text(doc_path: Path) -> str:
    xml = _read_content_xml(doc_path)
    root = _parse_xml(xml)

    body = root.find("office:body", NS)
    if body is None:
        return ""

    spreadsheet = body.find("office:spreadsheet", NS)
    if spreadsheet is None:
        return ""

    out_lines: list[str] = []
    for table in spreadsheet.findall("table:table", NS):
        sheet_name = table.attrib.get(f"{{{NS['table']}}}name", "Sheet")
        out_lines.append(f"## {sheet_name}")

        for row in table.findall("table:table-row", NS):
            row_repeat = _int_attr(row, f"{{{NS['table']}}}number-rows-repeated", 1)

            # Build one physical row, then repeat it row_repeat times.
            cells: list[str] = []
            for cell in row.findall("table:table-cell", NS):
                col_repeat = _int_attr(cell, f"{{{NS['table']}}}number-columns-repeated", 1)
                cell_text = " ".join("".join(p.itertext()).strip() for p in cell.findall("text:p", NS)).strip()
                for _ in range(max(1, col_repeat)):
                    cells.append(cell_text)

            rendered = "\t".join(cells).rstrip()
            for _ in range(max(1, row_repeat)):
                out_lines.append(rendered)

        out_lines.append("")  # blank line between sheets

    return "\n".join(out_lines).rstrip() + "\n"


def convert_one(doc_path: Path) -> str:
    ext = doc_path.suffix.lower()
    if ext == ".odt":
        return odt_to_text(doc_path)
    if ext == ".ods":
        return ods_to_text(doc_path)
    raise ValueError(f"Unsupported file type: {doc_path.name}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Convert .odt/.ods files to .txt for GitHub.")
    parser.add_argument("--in", dest="in_dir", default=".", help="Input directory (default: current directory)")
    parser.add_argument("--out", dest="out_dir", default="text", help="Output directory (default: text/)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .txt outputs")
    args = parser.parse_args(argv)

    in_dir = Path(args.in_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([*in_dir.glob("*.odt"), *in_dir.glob("*.ods")], key=lambda p: p.name.lower())
    if not files:
        print(f"No .odt/.ods files found in: {in_dir}")
        return 0

    converted = 0
    skipped = 0
    failed = 0

    for doc in files:
        out_path = out_dir / f"{doc.stem}.txt"
        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue

        try:
            text = convert_one(doc)
            out_path.write_text(text, encoding="utf-8")
            converted += 1
        except Exception as e:
            failed += 1
            print(f"ERROR: {doc.name}: {e}", file=sys.stderr)

    print(f"Done. converted={converted} skipped={skipped} failed={failed} -> {out_dir}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

