#!/usr/bin/env python3
"""
并行下载 marson2025 数据集从 S3 到本地
支持断点续传和进度追踪
"""

import boto3
import os
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore import UNSIGNED
from botocore.config import Config
import sys
import time

# 配置
BUCKET = 'genome-scale-tcell-perturb-seq'
PREFIX = 'marson2025_data/'
REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_DIR = REPO_ROOT / 'data' / 'marson2025_data'
MAX_WORKERS = 16  # 實測本沙盒總頻寬約 3-5 MB/s 見頂（1/16/32 併發分別得 0.9/3.1/4.5 MB/s），
                  # 提高並行度僅有限度換取吞吐；不要期待線性擴展
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks

def get_s3_client():
    """创建匿名 S3 客户端"""
    return boto3.client(
        's3',
        config=Config(
            signature_version=UNSIGNED,
            max_pool_connections=MAX_WORKERS * 2
        )
    )

def format_size(bytes_val):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"

def download_file(s3_client, key, local_path):
    """下载单个文件，支持断点续传"""
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # 检查文件是否存在且完整
    if local_path.exists():
        try:
            response_head = s3_client.head_object(Bucket=BUCKET, Key=key)
            remote_size = response_head['ContentLength']
            local_size = local_path.stat().st_size

            if local_size == remote_size:
                return local_path, True, remote_size  # 已完整
            elif local_size < remote_size:
                start_byte = local_size
            else:
                local_path.unlink()
                start_byte = 0
        except:
            start_byte = 0
    else:
        start_byte = 0

    # 下载
    try:
        if start_byte > 0:
            response = s3_client.get_object(
                Bucket=BUCKET,
                Key=key,
                Range=f'bytes={start_byte}-'
            )
            mode = 'ab'
        else:
            response = s3_client.get_object(Bucket=BUCKET, Key=key)
            mode = 'wb'

        total_size = response['ContentLength'] + start_byte
        downloaded = start_byte

        with open(local_path, mode) as f:
            for chunk in response['Body'].iter_chunks(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = (downloaded / total_size) * 100
                    print(f"  {local_path.name}: {pct:.1f}% ({format_size(downloaded)}/{format_size(total_size)})")

        return local_path, False, response['ContentLength']

    except Exception as e:
        print(f"  ❌ {key}: {e}")
        return local_path, False, 0

def main():
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📦 S3 数据下载器")
    print(f"   Source: s3://{BUCKET}/{PREFIX}")
    print(f"   Target: {LOCAL_DIR.absolute()}")
    print(f"   Workers: {MAX_WORKERS}\n")

    # 获取文件列表
    s3 = get_s3_client()
    print("🔍 扫描 S3 文件列表...")

    paginator = s3.get_paginator('list_objects_v2')
    files_to_download = []

    for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('/'):
                continue
            files_to_download.append((key, obj['Size']))

    total_bytes = sum(s for _, s in files_to_download)
    print(f"✓ 找到 {len(files_to_download)} 个文件，总大小 {format_size(total_bytes)}\n")

    # 检查本地已有的文件
    completed = 0
    completed_size = 0

    print("📊 检查已有文件...")
    for key, size in files_to_download:
        local_path = LOCAL_DIR / key.replace(PREFIX, '')
        if local_path.exists() and local_path.stat().st_size == size:
            completed += 1
            completed_size += size
            print(f"  ✓ {local_path.name}")

    if completed > 0:
        print(f"\n✓ 已有 {completed} 个文件完整，共 {format_size(completed_size)}")

    # 需要下载的文件
    remaining = [(k, s) for k, s in files_to_download if not (
        (LOCAL_DIR / k.replace(PREFIX, '')).exists() and
        (LOCAL_DIR / k.replace(PREFIX, '')).stat().st_size == s
    )]

    if not remaining:
        print("\n✅ 所有文件已完整！")
        return

    remaining_size = sum(s for _, s in remaining)
    print(f"\n⬇️  开始下载 {len(remaining)} 个文件 ({format_size(remaining_size)})...\n")

    start_time = time.time()
    downloaded = []
    resumed = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for key, _ in remaining:
            local_path = LOCAL_DIR / key.replace(PREFIX, '')
            future = executor.submit(
                download_file,
                get_s3_client(),
                key,
                local_path
            )
            futures[future] = (key, local_path)

        for future in as_completed(futures):
            key, local_path = futures[future]
            try:
                path, was_resumed, size = future.result()
                if was_resumed:
                    resumed.append((path.name, size))
                else:
                    downloaded.append((path.name, size))
                print(f"✓ 完成: {path.name} ({format_size(size)})")
            except Exception as e:
                print(f"❌ {key}: {e}")

    elapsed = time.time() - start_time
    speed = remaining_size / elapsed if elapsed > 0 else 0

    print(f"\n✅ 下载完成！")
    print(f"   用时: {elapsed/60:.1f} 分钟")
    print(f"   速度: {format_size(speed)}/s")
    print(f"   新下载: {len(downloaded)} 个 ({format_size(sum(s for _, s in downloaded))})")
    print(f"   续传: {len(resumed)} 个 ({format_size(sum(s for _, s in resumed))})")
    print(f"\n📍 数据位置: {LOCAL_DIR.absolute()}")

if __name__ == '__main__':
    main()
