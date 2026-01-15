#!/usr/bin/env python3
"""
PDF → TXT converter (text‑only, no GUI)

Usage (terminal):
    python app.py
"""

import os
import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    sys.exit(
        "PyPDF2 is not installed. Install dependencies with:\n"
        "    pip install -r requirements.txt"
    )


def pdf_to_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF file."""
    reader = PdfReader(str(pdf_path))
    text_parts = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
            if text:
                text_parts.append(text)
            else:
                # Some PDFs contain only images; we just note the empty page.
                text_parts.append(f"[Page {page_num} contains no extractable text]\n")
        except Exception as exc:
            text_parts.append(f"[Error extracting page {page_num}: {exc}]\n")
    return "\n".join(text_parts)


def main() -> None:
    # --------------------------------------------------------------
    # 1️⃣ Prompt the user for the PDF location
    # --------------------------------------------------------------
    pdf_input = input("Enter the path to the PDF file (relative or absolute): ").strip()
    pdf_path = Path(pdf_input).expanduser().resolve()

    if not pdf_path.is_file():
        print(f"❌  File not found: {pdf_path}")
        sys.exit(1)

    # --------------------------------------------------------------
    # 2️⃣ Convert PDF → text
    # --------------------------------------------------------------
    print(f"🔎  Extracting text from '{pdf_path.name}' …")
    extracted_text = pdf_to_text(pdf_path)

    # --------------------------------------------------------------
    # 3️⃣ Write output .txt file (same folder, same base name)
    # --------------------------------------------------------------
    txt_path = pdf_path.with_suffix(".txt")
    try:
        txt_path.write_text(extracted_text, encoding="utf-8")
        print(f"✅  Text saved to: {txt_path}")
    except Exception as exc:
        print(f"❌  Failed to write output file: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()