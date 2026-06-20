"""Single-process sequential converter — just works."""
import subprocess
import sys
import time
import os
from pathlib import Path

OUT_DIR = Path(r"c:/李学恒端午ai班/原始文件")
SCRIPT = Path(r"c:/李学恒端午ai班/.claude/skills/pdf-to-markdown/scripts/convert_pdf.py")

env = {**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}

pdfs = sorted(p for p in OUT_DIR.glob("chunk_*.pdf")
              if not p.with_suffix(".md").exists()
              or p.with_suffix(".md").stat().st_size == 0)

print(f"{len(pdfs)} chunks to process\n")

ok = 0
t0 = time.time()
for i, pdf in enumerate(pdfs, 1):
    md = pdf.with_suffix(".md")
    t1 = time.time()
    r = subprocess.run([sys.executable, str(SCRIPT), str(pdf), str(md)],
                       capture_output=True, text=True, timeout=1200,
                       env=env, encoding="utf-8", errors="replace")
    dt = time.time() - t1
    if r.returncode == 0 and md.exists():
        kb = md.stat().st_size / 1024
        ok += 1
        print(f"[{i}/{len(pdfs)}] OK {pdf.stem} ({kb:.0f}KB, {dt:.0f}s)", flush=True)
    else:
        print(f"[{i}/{len(pdfs)}] FAIL {pdf.stem} rc={r.returncode}", flush=True)

print(f"\nDone! {ok}/{len(pdfs)} OK in {(time.time()-t0)/60:.0f} min")
