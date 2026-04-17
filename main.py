"""
金融市场多Agent仿真系统
用法: python main.py "美联储宣布加息50基点"
"""
import sys
import os
import glob

from dotenv import load_dotenv
load_dotenv()

from src.graph.main_graph import build_graph


def discover_agents(agents_dir: str = "agents") -> dict[str, str]:
    """自动发现 agents/ 目录下的所有 .md 配置文件"""
    configs = {}
    for md_path in sorted(glob.glob(os.path.join(agents_dir, "*.md"))):
        # 从文件名提取 agent_id
        agent_id = os.path.splitext(os.path.basename(md_path))[0]
        configs[agent_id] = md_path
    return configs


def main():
    if len(sys.argv) < 2:
        news = "美联储宣布加息50基点，超出市场预期的25基点"
        print(f"[未提供消息，使用默认] {news}\n")
    else:
        news = sys.argv[1]

    agent_configs = discover_agents()
    print(f"已发现 {len(agent_configs)} 个 Agent: {list(agent_configs.keys())}\n")

    graph = build_graph()

    print("=" * 60)
    print(f"消息: {news}")
    print("=" * 60)

    result = graph.invoke({
        "raw_news": news,
        "news_signal": None,
        "agent_configs": agent_configs,
        "responses": [],
        "report": None,
    })

    # 打印信号提取结果
    print("\n📡 信号提取:")
    signal = result["news_signal"]
    print(f"  方向: {signal['direction']} | 强度: {signal['intensity']} | 置信度: {signal['confidence']}")
    print(f"  受影响资产: {', '.join(signal['affected_assets'])}")
    print(f"  摘要: {signal['summary']}")

    # 打印每个 Agent 的响应
    print("\n" + "=" * 60)
    print("📊 各群体决策意向:")
    print("=" * 60)
    for r in result["responses"]:
        stance_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
        emoji = stance_emoji.get(r["stance"], "⚪")
        print(f"\n{emoji} {r['agent_name']} ({r['agent_id']})")
        print(f"  立场: {r['stance']} | 置信度: {r['confidence']} | 强度: {r['intensity']}")
        print(f"  操作: {r['action']}")
        print(f"  推理: {r['reasoning'][:200]}...")
        print(f"  时间: {r['time_horizon']} | 资产: {', '.join(r['affected_assets'])}")

    # 打印报告
    print("\n" + "=" * 60)
    print("📋 综合分析报告:")
    print("=" * 60)
    print(result["report"])


if __name__ == "__main__":
    main()
