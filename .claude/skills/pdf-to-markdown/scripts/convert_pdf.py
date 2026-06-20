"""
PDF to Markdown converter with automatic OCR fallback for scanned/image-based PDFs.

Usage:
    python convert_pdf.py <input.pdf> [output.md] [--pages N] [--dpi 300]

If --pages is not specified, converts all pages.
If output.md is not specified, uses the input filename with .md extension.
"""

# MUST be set before any library imports that load OpenMP (PyMuPDF, EasyOCR, etc.)
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import argparse
import sys
from pathlib import Path


def detect_pdf_type(doc) -> str:
    """Check first 3 pages to determine if PDF is text-based or image-based."""
    import fitz
    text_chars = 0
    image_count = 0
    for i in range(min(3, doc.page_count)):
        page = doc[i]
        text = page.get_text()
        text_chars += len(text.strip())
        image_count += len(page.get_images())
    # If average text per page < 50 chars and has images, treat as scanned
    avg_text = text_chars / min(3, doc.page_count)
    if avg_text < 50 and image_count > 0:
        return "scanned"
    return "text"


def convert_text_pdf(doc, total_pages: int, out_path: Path):
    """Convert text-based PDF using markitdown or PyMuPDF fallback."""
    import fitz
    lines = [
        f"# PDF 转换结果\n\n",
        f"> 源文件: {out_path.stem}.pdf | 共 {total_pages} 页 | 文字型PDF\n\n---\n",
    ]
    for i in range(total_pages):
        page = doc[i]
        text = page.get_text("text")
        lines.append(f"## 第 {i + 1} 页\n\n")
        lines.append(text.strip() if text.strip() else "*(本页无文字)*")
        lines.append("\n\n---\n")
    out_path.write_text("".join(lines), encoding="utf-8")


def convert_scanned_pdf(doc, total_pages: int, out_path: Path, dpi: int = 300):
    """Convert scanned/image-based PDF using OCR (EasyOCR)."""
    import fitz
    import easyocr
    import numpy as np
    import gc

    print("Loading EasyOCR (Chinese + English)...")
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)

    lines = [
        f"# PDF 转换结果\n\n",
        f"> 源文件: {out_path.stem}.pdf | 共 {total_pages} 页 | 扫描件OCR识别\n\n---\n",
    ]

    for i in range(total_pages):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)

        # Convert pixmap directly to numpy array (RGB) without writing to disk
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        # EasyOCR expects RGB; pix.samples from PyMuPDF are already RGB
        if pix.n == 4:
            img_array = img_array[:, :, :3]  # drop alpha if present

        results = reader.readtext(img_array)
        text = "\n".join([r[1] for r in results])

        lines.append(f"## 第 {i + 1} 页\n\n")
        lines.append(text.strip() if text.strip() else "*(本页无可识别文字)*")
        lines.append("\n\n---\n")

        # Free memory
        del pix, img_array
        gc.collect()
        print(f"  Page {i + 1}/{total_pages} done ({len(text)} chars)")

    out_path.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown (auto-detects text vs scanned)"
    )
    parser.add_argument("input", type=str, help="Path to input PDF file")
    parser.add_argument("output", nargs="?", type=str, default=None,
                        help="Path to output .md file (default: same name as input)")
    parser.add_argument("--pages", "-p", type=int, default=None,
                        help="Number of pages to convert (default: all)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI for rendering scanned pages (default: 300)")
    parser.add_argument("--force-ocr", action="store_true",
                        help="Force OCR even if PDF appears text-based")
    args = parser.parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Error: file not found: {src}")
        sys.exit(1)

    out_path = Path(args.output).resolve() if args.output else src.with_suffix(".md")

    # Check dependencies
    try:
        import fitz
    except ImportError:
        print("PyMuPDF (fitz) is required. Install: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(str(src))
    total = doc.page_count
    pages_to_convert = min(args.pages or total, total)

    print(f"PDF: {src.name}")
    print(f"Total pages: {total}, converting: {pages_to_convert}")

    pdf_type = detect_pdf_type(doc) if not args.force_ocr else "scanned"
    print(f"Detected type: {pdf_type}")

    # Slice to requested pages if needed
    if args.pages and args.pages < total:
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=0, to_page=pages_to_convert - 1)
        doc.close()
        doc = new_doc
        total = pages_to_convert

    if pdf_type == "text":
        convert_text_pdf(doc, total, out_path)
    else:
        convert_scanned_pdf(doc, total, out_path, dpi=args.dpi)

    doc.close()

    size_kb = out_path.stat().st_size / 1024
    print(f"\nDone: {out_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
