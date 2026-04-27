#!/usr/bin/env bash
# 单个事件仿真：一条新闻 → 6类agent群体决策意向 + 综合报告
# 用法:
#   bash scenarios/single_event.sh
#   bash scenarios/single_event.sh "你的自定义新闻"

set -euo pipefail
cd "$(dirname "$0")/.."

NEWS="${1:-美联储宣布加息50基点，超出市场预期的25基点}"

echo "=========================================="
echo "  单事件仿真 (single mode)"
echo "=========================================="
echo "新闻: $NEWS"
echo ""

python main.py "$NEWS" --mode single
