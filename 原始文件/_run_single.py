"""Single-threaded sequential PDF chunk converter — won't OOM your GPU."""
import subprocess
import sys
import time
import os
from pathlib import Path

OUT_DIR = Path(r"c:/李学恒端午ai班/原始文件")
SCRIPT = Path(r"c:/李学恒端午ai班/.claude/skills/pdf-to-markdown/scripts/convert_pdf.py")
env = {**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"}

chunks = sorted(
    p for p in OUT_DIR.glob("chunk_*.pdf")
    if not p.with_suffix(".md").exists() or p.with_suffix(".md").stat().st_size == 0
)

print(f"Single-threaded | {len(chunks)} chunks to process\n")

total_ok = 0
total_fail = 0
t_start = time.time()

for idx, pdf in enumerate(chunks, 1):
    md = pdf.with_suffix(".md")
    label = pdf.stem
    t0 = time.time()

    print(f"[{idx}/{len(chunks)}] Processing {label} ...", flush=True)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(pdf), str(md)],
        capture_output=True, text=True, timeout=1200, env=env, encoding="utf-8",
    )
    elapsed = time.time() - t0

    if r.returncode == 0 and md.exists():
        kb = md.stat().st_size / 1024
        print(f"  ✓ OK  ({kb:.0f}KB, {elapsed:.0f}s)", flush=True)
        total_ok += 1
    else:
        print(f"  ✗ FAIL  rc={r.returncode}", flush=True)
        if r.stderr:
            print(f"  stderr: {r.stderr[-300:]}", flush=True)
        total_fail += 1

total_elapsed = time.time() - t_start
print(f"\n{'='*50}")
print(f"Done! OK: {total_ok}, FAIL: {total_fail}, Time: {total_elapsed/60:.1f} min")
