---
name: pdf-to-markdown
description: Convert PDF files to Markdown format, automatically handling both text-based and scanned/image-based PDFs. Use this skill whenever the user asks to convert a PDF to Markdown, extract text from a PDF, OCR a scanned PDF, or turn PDF content into readable markdown — even if they don't explicitly say "OCR", because many PDFs are scanned images without a text layer.
---

# PDF to Markdown Converter

Convert any PDF to a clean Markdown file, with automatic OCR fallback for scanned/image-based documents.

## Quick start

Use the bundled script for deterministic, reliable conversion:

```bash
python scripts/convert_pdf.py <input.pdf> [output.md] [--pages N] [--dpi 300] [--force-ocr]
```

The script auto-detects whether the PDF has a text layer or is image-only, then picks the right method.

## When conversion produces empty output

If markitdown or PyMuPDF text extraction returns empty/near-empty results, the PDF is likely a **scanned document** — each page is an image with no embedded text. The bundled script handles this automatically:

1. **Detect**: Reads first 3 pages to check if text exists
2. **Text-based** → extracts text directly via PyMuPDF
3. **Scanned (image-based)** → renders each page at 300 DPI as an image, then runs EasyOCR (Chinese + English) to extract text

## Dependencies

Install what's missing based on the error message. Typical first-time setup:

```bash
pip install pymupdf easyocr markitdown
```

- `pymupdf` (fitz) — PDF reading, text extraction, page rendering
- `easyocr` — OCR engine for scanned pages (pure Python, no system deps needed)
- `markitdown` — optional, for enhanced text-based conversion

## Output format

Every conversion produces a structured markdown file:

```
# PDF 转换结果
> 源文件: xxx.pdf | 共 N 页 | 类型标识

---
## 第 1 页
(content...)
---
## 第 2 页
(content...)
---
```

## Known issues

- **OMP duplicate lib error** (`KMP_DUPLICATE_LIB_OK`): The script already sets this env var. If you see this error, run with `KMP_DUPLICATE_LIB_OK=TRUE python ...`
- **EasyOCR model download**: First run downloads detection/recognition models (~100-200 MB). This is one-time — subsequent runs use cached models.
- **GPU acceleration**: EasyOCR defaults to GPU if CUDA is available, otherwise CPU. Scanned PDFs on CPU are slower (~10-30s per page at 300 DPI) but produce better results.
- **OCR accuracy**: Chinese + English OCR is good but not perfect. Characters like 马/苋, 王/壬 may be confused. For archival-quality conversion, consider Azure Document Intelligence or similar paid services.

## Tips for best results

- Use `--dpi 200` for faster but slightly less accurate OCR on large documents
- Use `--dpi 300` (default) for the best accuracy/speed balance
- Use `--pages N` to test the first few pages before converting an entire document
- Use `--force-ocr` if a text-based PDF has garbled extractable text (e.g., embedded fonts with bad encoding)
