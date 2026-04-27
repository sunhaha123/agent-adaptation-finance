#!/usr/bin/env bash
# 事件串仿真：多阶段事件链 → 遗传演化 + 订单簿撮合 + 涌现报告
# 用法:
#   bash scenarios/event_chain.sh                          # 使用内置美伊战争事件串
#   bash scenarios/event_chain.sh --file my_events.txt     # 从文件读取事件串
#   bash scenarios/event_chain.sh --news "自定义新闻"       # 单条新闻自动扩展为事件链

set -euo pipefail
cd "$(dirname "$0")/.."

POPULATION=120
ROUNDS=50
GENERATIONS=20
SEED=42
EVENTS=8
MODE="builtin"
NEWS=""
FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)      FILE="$2";        MODE="file";  shift 2 ;;
        --news)      NEWS="$2";        MODE="news";  shift 2 ;;
        --pop)       POPULATION="$2";  shift 2 ;;
        --rounds)    ROUNDS="$2";      shift 2 ;;
        --gens)      GENERATIONS="$2"; shift 2 ;;
        --events)    EVENTS="$2";      shift 2 ;;
        --seed)      SEED="$2";        shift 2 ;;
        -h|--help)
            echo "用法: bash scenarios/event_chain.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --file FILE    从文件读取事件串（每行一个事件，格式: 标题：描述）"
            echo "  --news TEXT    单条新闻，由LLM自动扩展为事件链"
            echo "  --pop N        种群大小 (默认: 120)"
            echo "  --rounds N     每代交易轮数 (默认: 50)"
            echo "  --gens N       遗传代数 (默认: 20)"
            echo "  --events N     事件链节点数 (默认: 8)"
            echo "  --seed N       随机种子 (默认: 42)"
            echo ""
            echo "不带参数运行则使用内置美伊战争事件串示例。"
            exit 0 ;;
        *)           echo "未知参数: $1"; exit 1 ;;
    esac
done

echo "=========================================="
echo "  事件串仿真 (evolve mode)"
echo "=========================================="
echo "种群=$POPULATION | 轮数=$ROUNDS | 代数=$GENERATIONS | 种子=$SEED"
echo ""

case "$MODE" in
    file)
        echo "事件源: 文件 $FILE"
        echo ""
        python main.py --events-file "$FILE" \
            --mode evolve \
            --population "$POPULATION" \
            --rounds "$ROUNDS" \
            --generations "$GENERATIONS" \
            --events "$EVENTS" \
            --seed "$SEED"
        ;;
    news)
        echo "事件源: 自定义新闻 → LLM扩展"
        echo "新闻: $NEWS"
        echo ""
        python main.py "$NEWS" \
            --mode evolve \
            --population "$POPULATION" \
            --rounds "$ROUNDS" \
            --generations "$GENERATIONS" \
            --events "$EVENTS" \
            --seed "$SEED"
        ;;
    builtin)
        EVENTS_TEXT=$(cat <<'EOF'
前期对抗升级：美伊关系恶化，地区驻军、舰队与防空力量加强部署，市场开始计入中东地缘风险溢价。
战争爆发：美国与以色列对伊朗关键军事/核相关/指挥目标实施打击，冲突从威慑转为公开战争。
伊朗报复：伊朗以导弹、无人机、代理武装等方式反击美以目标，战争进入双向升级阶段。
停火窗口出现：在多方调停下，双方接受临时停火或降烈度安排，市场开始交易"最坏情形避免"。
EOF
)
        echo "事件源: 内置美伊战争事件串（4阶段）"
        echo ""
        python main.py "$EVENTS_TEXT" \
            --mode evolve \
            --population "$POPULATION" \
            --rounds "$ROUNDS" \
            --generations "$GENERATIONS" \
            --events "$EVENTS" \
            --seed "$SEED"
        ;;
esac
