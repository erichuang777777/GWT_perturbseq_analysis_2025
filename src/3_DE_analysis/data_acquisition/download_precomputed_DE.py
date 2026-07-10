#!/usr/bin/env python3
"""
只下載任務 A 真正需要的檔案：原始資料提供者已預先算好的
target×gene 帶符號 DE 矩陣（GWCD4i.DE_stats.h5ad），而非重跑 1.67TB
單細胞原始資料的三步 pipeline。

發現：GWCD4i.DE_stats.h5ad 本身就含有 obs=33,983 target×condition、
var=10,282 genes，layers 有 log_fc/p_value/adj_p_value/baseMean/lfcSE/zscore
——正是 TASK_A_RUNBOOK_GB10.md 要重跑產出的東西。只要 15.63GB，不必動 1.67TB。

用多段 range request 並發下載（純 requests，非 boto3——實測 boto3 單流
0.9MB/s、32併發僅4.5MB/s；同一檔案用 requests 24 併發可達 ~15.5MB/s）。
"""

import json
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BUCKET_URL = "https://genome-scale-tcell-perturb-seq.s3.amazonaws.com/marson2025_data"
REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_DIR = REPO_ROOT / "data" / "marson2025_data"

# 只抓這幾個檔案——不是全部 14 個 h5ad
FILES = [
    "GWCD4i.DE_stats.h5ad",                                  # 15.63 GB - 核心：target×gene signed DE 矩陣
    "suppl_tables/DE_stats.suppl_table.csv",                 # 4.8 MB  - 對照用的聚合表（已在 repo 有，驗證一致性用）
    "suppl_tables/sample_metadata.suppl_table.csv",          # 2.9 KB
    "suppl_tables/sgrna_library_metadata.suppl_table.csv",   # 9.9 MB  - guide/target 別名解析
    "data_sharing_readme.md",                                # 27 KB   - schema 說明
    "GWCD4i.pseudobulk_merged.h5ad",                          # 41.51 GB - GEARS 需要真實表現量矩陣，非 DE 統計
]

N_WORKERS = 24          # 實測本沙盒此區間吞吐最佳（~15.5 MB/s；40 併發反而略降）
CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB per range request


def format_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def get_remote_size(url):
    r = requests.head(url, timeout=30)
    r.raise_for_status()
    return int(r.headers["Content-Length"])


def fetch_range_write(url, start, end, fh, lock, max_retries=5):
    """抓取一段 range，立刻 seek 寫入目標檔案的對應位置——不在記憶體累積整檔。
    對 S3 偶發的 503/连线重置做指数退避重試（長時間大檔下載常見的瞬時錯誤，
    不重試的話單一 chunk 失敗就會讓已下載的一大段前功盡棄）。"""
    last_exc = None
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=120)
            r.raise_for_status()
            content = r.content
            with lock:
                fh.seek(start)
                fh.write(content)
            return len(content)
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 30))
    raise last_exc


def download_file(key):
    import threading

    url = f"{BUCKET_URL}/{key}"
    local_path = LOCAL_DIR / key
    local_path.parent.mkdir(parents=True, exist_ok=True)

    total_size = get_remote_size(url)

    if local_path.exists() and local_path.stat().st_size == total_size:
        print(f"✓ 已存在且完整: {key} ({format_size(total_size)})", flush=True)
        return

    print(f"⬇ 開始: {key} ({format_size(total_size)})", flush=True)
    start_t = time.time()

    n_chunks = max(1, (total_size + CHUNK_SIZE - 1) // CHUNK_SIZE)
    ranges = [(i * CHUNK_SIZE, min(i * CHUNK_SIZE + CHUNK_SIZE - 1, total_size - 1)) for i in range(n_chunks)]

    tmp_path = local_path.with_suffix(local_path.suffix + ".part")
    manifest_path = local_path.with_suffix(local_path.suffix + ".manifest.json")

    # 斷點續傳：manifest 記錄「已成功寫入」的 chunk 編號。中斷重啟時，
    # 只要 .part 檔大小、總大小都對得上，就跳過 manifest 裡已完成的
    # chunk，不必整檔重來（先前兩次中斷──一次 S3 503、一次背景任務被
    # 強制終止──都因為沒有這個機制而必須重下整個 41.5GB，太浪費）。
    completed_chunks = set()
    if manifest_path.exists() and tmp_path.exists() and tmp_path.stat().st_size == total_size:
        try:
            completed_chunks = set(json.loads(manifest_path.read_text()))
            print(f"  發現續傳紀錄：已完成 {len(completed_chunks)}/{n_chunks} 個 chunk", flush=True)
        except Exception:
            completed_chunks = set()
    else:
        # 大小對不上（不同檔案或全新下載）——重新配置檔案大小，清空續傳紀錄
        with open(tmp_path, "wb") as f:
            f.truncate(total_size)
        manifest_path.write_text("[]")

    lock = threading.Lock()
    manifest_lock = threading.Lock()
    downloaded = sum(
        (ranges[i][1] - ranges[i][0] + 1) for i in completed_chunks if i < len(ranges)
    )

    def mark_done(idx):
        with manifest_lock:
            completed_chunks.add(idx)
            manifest_path.write_text(json.dumps(sorted(completed_chunks)))

    with open(tmp_path, "r+b") as fh:
        with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
            futures = {
                ex.submit(fetch_range_write, url, s, e, fh, lock): idx
                for idx, (s, e) in enumerate(ranges)
                if idx not in completed_chunks
            }
            done = len(completed_chunks)
            for fut in as_completed(futures):
                idx = futures[fut]
                downloaded += fut.result()
                mark_done(idx)
                done += 1
                if done % 10 == 0 or done == n_chunks:
                    pct = done / n_chunks * 100
                    elapsed = time.time() - start_t
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    print(f"  {key}: {pct:.0f}% ({format_size(downloaded)}/{format_size(total_size)}, {format_size(speed)}/s)", flush=True)

    tmp_path.rename(local_path)
    manifest_path.unlink(missing_ok=True)

    elapsed = time.time() - start_t
    print(f"✅ 完成: {key} — {format_size(total_size)} in {elapsed/60:.1f} min ({format_size(total_size/elapsed)}/s)\n", flush=True)


def main():
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"目標檔案（{len(FILES)} 個，非全部 14 個原始 h5ad）：")
    for f in FILES:
        print(f"  - {f}")
    print()

    for key in FILES:
        for attempt in range(3):
            try:
                download_file(key)
                break
            except Exception as e:
                print(f"❌ {key}（第 {attempt+1}/3 次嘗試）: {e}", flush=True)
                if attempt < 2:
                    time.sleep(15)

    print("全部完成。位置：", LOCAL_DIR)


if __name__ == "__main__":
    main()
