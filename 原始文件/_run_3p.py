"""3-worker parallel OCR — processes remaining chunks with proper naming handling."""
import subprocess
import sys
import time
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import freeze_support

OUT_DIR = Path(r"c:/李学恒端午ai班/原始文件")
SCRIPT = Path(r"c:/李学恒端午ai班/.claude/skills/pdf-to-markdown/scripts/convert_pdf.py")
WORKERS = 3

env = {
    **os.environ,
    "KMP_DUPLICATE_LIB_OK": "TRUE",
    "OMP_NUM_THREADS": "2",
    "MKL_NUM_THREADS": "2",
}


def find_unprocessed_chunks(out_dir):
    """Find PDF chunks that don't have ANY existing .md file.
    Handles both naming conventions: chunk_01.md and chunk_01_p1-p10.md
    Output uses PDF stem: chunk_11_p101-p110.pdf -> chunk_11_p101-p110.md
    """
    all_pdfs = sorted(out_dir.glob("chunk_*.pdf"))
    # Build set of chunk numbers that already have .md output
    existing_mds = set()
    for md in out_dir.glob("chunk_*.md"):
        stem = md.stem  # e.g. "chunk_05" or "chunk_05_p41-p50"
        parts = stem.split("_")
        if len(parts) >= 2:
            existing_mds.add(parts[1])  # chunk number like "05"

    unprocessed = []
    skipped = 0
    for pdf in all_pdfs:
        stem = pdf.stem
        parts = stem.split("_")
        chunk_num = parts[1] if len(parts) >= 2 else ""
        if chunk_num in existing_mds:
            skipped += 1
            continue
        md_path = pdf.with_suffix(".md")
        unprocessed.append((pdf, md_path))

    if skipped:
        print(f"  (skipped {skipped} already-processed chunks)")
    return unprocessed


def convert_batch(worker_id, tasks):
    """Process a batch of (pdf_path, md_path) tuples sequentially."""
    ok = 0
    fail = 0
    failed = []
    log_lines = [f"Worker {worker_id} starting {len(tasks)} chunks"]

    for idx, (pdf, md) in enumerate(tasks, 1):
        t0 = time.time()
        label = pdf.stem
        log_lines.append(f"  [{idx}/{len(tasks)}] {label}")

        r = subprocess.run(
            [sys.executable, str(SCRIPT), str(pdf), str(md), "--dpi", "200"],
            capture_output=True, text=True, timeout=1200, env=env,
            encoding="utf-8", errors="replace",
        )
        elapsed = time.time() - t0

        if r.returncode == 0 and md.exists():
            kb = md.stat().st_size / 1024
            log_lines.append(f"    OK ({kb:.0f}KB, {elapsed:.0f}s)")
            ok += 1
        else:
            err = r.stderr[-300:] if r.stderr else "none"
            log_lines.append(f"    FAIL rc={r.returncode} err={err}")
            fail += 1
            failed.append(label)

    log_lines.append(f"Worker {worker_id} DONE. OK={ok} FAIL={fail}")
    return ok, fail, failed, log_lines


def main():
    tasks = find_unprocessed_chunks(OUT_DIR)
    print(f"Total chunks to process: {len(tasks)}")
    print(f"Workers: {WORKERS} (each limited to 2 CPU threads)")

    if not tasks:
        print("All chunks already processed!")
        return

    # Split tasks into 3 batches (round-robin)
    batches = [[] for _ in range(WORKERS)]
    for i, task in enumerate(tasks):
        batches[i % WORKERS].append(task)

    for i, batch in enumerate(batches):
        names = [pdf.stem for pdf, _ in batch]
        print(f"Worker {i}: {len(batch)} chunks — {' '.join(names)}")

    t_start = time.time()

    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futures = {
            ex.submit(convert_batch, i, batch): i
            for i, batch in enumerate(batches) if batch
        }
        for f in as_completed(futures):
            worker_id = futures[f]
            try:
                ok, fail, failed, log_lines = f.result()
                print(f"\n--- Worker {worker_id}: OK={ok} FAIL={fail} ---")
                for line in log_lines:
                    print(line)
            except Exception as e:
                print(f"\n--- Worker {worker_id} CRASHED: {e} ---")

    elapsed = time.time() - t_start
    n_md = len(list(OUT_DIR.glob("chunk_*.md")))
    print(f"\n{'='*60}")
    print(f"DONE! {n_md} MD files in {elapsed/60:.1f} min")


if __name__ == "__main__":
    freeze_support()
    main()
