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
疫情信号出现：武汉发现不明原因肺炎。 2019年12月底，中国武汉报告聚集性肺炎病例，市场最初未充分定价，全球风险资产仍处于偏乐观状态。
中国疫情确认扩散：病毒确认并出现人传人判断。 2020年1月中旬，病例扩大，中国确认新型冠状病毒可人传人，亚洲市场率先承压，避险情绪开始抬头。
武汉封城：疫情从局部卫生事件升级为重大冲击。 2020年1月23日，武汉实施封城，随后湖北多地管控，全球供应链风险开始显性化。
全球公共卫生警报：WHO宣布国际关注的突发公共卫生事件。 2020年1月30日，WHO宣布PHEIC，市场开始担心跨国传播，但美股当时仍未完全转向恐慌。
中国停工与供应链中断：制造业冲击外溢。 2020年2月上旬至中旬，中国春节后复工延迟，电子、汽车、消费品供应链受影响，美股开始重新评估企业盈利风险。
疫情向欧美扩散：意大利、韩国、伊朗病例激增。 2020年2月下旬，疫情从中国主导转为多国爆发，全球市场风险偏好快速恶化，美股进入急跌阶段。
美国疫情暴露：社区传播与检测不足引发恐慌。 2020年3月初，美国本土病例增加，检测体系滞后，市场从“海外冲击”转为“美国本土经济停摆风险”。
全球金融踩踏：美股暴跌并多次熔断。 2020年3月9日至3月18日，美股多次触发熔断，流动性压力、油价暴跌、信用风险和疫情封锁预期叠加。
政策全面救市：美联储与美国财政部强力干预。 2020年3月中下旬，美联储紧急降息至接近零、启动大规模QE，美国通过约2万亿美元CARES Act，美股在3月23日前后见阶段性底部。
疫情常态化与复工交易：市场从崩盘转向流动性驱动反弹。 2020年4月至5月，美国失业数据恶化、企业盈利下修，但市场开始押注财政货币托底、科技股受益、经济逐步重启，纳指和标普明显反弹
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
