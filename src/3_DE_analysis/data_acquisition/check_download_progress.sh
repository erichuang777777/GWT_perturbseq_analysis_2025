#!/bin/bash
# 实时监视下载进度
# 執行位置：repo 根目錄或本目錄皆可（自動定位 repo 根）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DATA_DIR="$REPO_ROOT/data/marson2025_data"
EXPECTED_SIZE=1673.8  # GB

while true; do
    clear
    echo "📦 下载进度监视"
    echo "=================================="

    current_size=$(du -sb "$DATA_DIR" 2>/dev/null | awk '{print $1}')
    current_gb=$(echo "scale=1; $current_size / 1024 / 1024 / 1024" | bc)
    file_count=$(find "$DATA_DIR" -type f | wc -l)

    echo "已下载: $current_gb GB / $EXPECTED_SIZE GB"
    echo "文件数: $file_count / 14"

    # 计算进度百分比
    percent=$(echo "scale=1; $current_gb * 100 / $EXPECTED_SIZE" | bc)
    echo "进度: $percent %"

    echo ""
    echo "最近下载的文件:"
    ls -lhS "$DATA_DIR" 2>/dev/null | tail -5 | awk '{print "  " $9, "(" $5 ")"}'

    echo ""
    echo "后台进程状态:"
    ps aux | grep download_s3_data.py | grep -v grep || echo "  (已完成或未运行)"

    echo ""
    echo "按 Ctrl+C 退出，或等待 30 秒后刷新..."
    sleep 30
done
