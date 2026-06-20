"""Process all PDF chunks: 4 parallel workers, each spawns a subprocess."""
import subprocess, sys, time, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT_DIR = Path(r"c:/李学恒端午ai班/原始文件")
SCRIPT = Path(r"c:/李学恒端午ai班/.claude/skills/pdf-to-markdown/scripts/convert_pdf.py")
WORKERS = 4
env = {**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"}

chunks = sorted(
    p for p in OUT_DIR.glob("chunk_*.pdf")
    if not p.with_suffix(".md").exists() or p.with_suffix(".md").stat().st_size == 0
)
print(f"To process: {len(chunks)} chunks | Workers: {WORKERS}\n")

done = [0]

def convert(pdf):
    md = pdf.with_suffix(".md")
    label = pdf.stem
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(pdf), str(md)],
        capture_output=True, text=True, timeout=900, env=env, encoding="utf-8",
    )
    elapsed = time.time() - t0
    done[0] += 1
    n = done[0]
    if r.returncode == 0 and md.exists():
        kb = md.stat().st_size / 1024
        print(f"[{n:2d}/{len(chunks)}] OK  {label}  ({kb:.0f}KB, {elapsed:.0f}s)")
    else:
        print(f"[{n:2d}/{len(chunks)}] FAIL {label}  rc={r.returncode}")
    return r.returncode == 0

t0 = time.time()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(convert, p): p for p in chunks}
    for f in as_completed(futures):
        f.result()

elapsed = time.time() - t0
n_md = len(list(OUT_DIR.glob("*.md")))
print(f"\nDone! {n_md} MD files in {elapsed/60:.1f} min")
