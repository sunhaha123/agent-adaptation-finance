"""
金融市场多Agent仿真系统
用法: python main.py "美联储宣布加息50基点"
"""
import argparse
import os
import glob
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


def discover_agents(agents_dir: str = "agents") -> dict[str, str]:
    """自动发现 agents/ 目录下的所有 .md 配置文件"""
    configs = {}
    for md_path in sorted(glob.glob(os.path.join(agents_dir, "*.md"))):
        # 从文件名提取 agent_id
        agent_id = os.path.splitext(os.path.basename(md_path))[0]
        configs[agent_id] = md_path
    return configs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="金融市场多 Agent 仿真系统")
    parser.add_argument(
        "news",
        nargs="?",
        help="待仿真的市场新闻",
    )
    parser.add_argument(
        "--mode",
        choices=["single", "evolve"],
        default="single",
        help="single=原有单轮决策意向；evolve=多轮订单簿+遗传算法仿真",
    )
    parser.add_argument("--rounds", type=int, default=50, help="evolve 模式每代交易轮数")
    parser.add_argument("--generations", type=int, default=20, help="evolve 模式遗传代数")
    parser.add_argument("--population", type=int, default=120, help="evolve 模式个体数量")
    parser.add_argument("--events", type=int, default=8, help="evolve 模式事件链节点数量")
    parser.add_argument("--events-file", help="从文本文件读取用户自定义事件串")
    parser.add_argument("--seed", type=int, default=42, help="evolve 模式随机种子")
    return parser.parse_args()


def run_single(news: str, agent_configs: dict[str, str]) -> None:
    from src.graph.main_graph import build_graph

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


def run_evolve(news: str, agent_configs: dict[str, str], args: argparse.Namespace) -> None:
    from src.simulation import run_evolution_mode
    from src.simulation.events import format_event_line

    print("=" * 60)
    print(f"消息: {news}")
    print("=" * 60)
    print(
        f"模式: evolve | population={args.population} | "
        f"rounds={args.rounds} | generations={args.generations} | seed={args.seed}"
    )

    result = run_evolution_mode(
        raw_news=news,
        agent_configs=agent_configs,
        population_size=args.population,
        rounds_per_generation=args.rounds,
        generations=args.generations,
        event_count=args.events,
        seed=args.seed,
    )

    signal = result.news_signal
    print("\n📡 信号提取:")
    print(f"  方向: {signal['direction']} | 强度: {signal['intensity']} | 置信度: {signal['confidence']}")
    print(f"  受影响资产: {', '.join(signal['affected_assets'])}")
    print(f"  摘要: {signal['summary']}")

    print("\n" + "=" * 60)
    print("🧭 事件串:")
    print("=" * 60)
    for event in result.event_timeline:
        print(f"  {event.step + 1}. {format_event_line(event)}")
        print(
            f"     信号={event.direction} | 强度={event.intensity:.2f} | "
            f"置信度={event.confidence:.2f} | 轮次={event.rounds}"
        )

    print("\n" + "=" * 60)
    print("🧬 遗传演化摘要:")
    print("=" * 60)
    for summary in result.generation_summaries:
        print(
            f"第 {summary.generation} 代 | "
            f"价格 {summary.start_price:.2f}->{summary.end_price:.2f} | "
            f"best fitness={summary.best_fitness:.4f} | "
            f"avg fitness={summary.avg_fitness:.4f} | "
            f"羊群={summary.avg_herd_index:.3f} | "
            f"成交量={summary.total_volume:.2f}"
        )

    if result.market_history:
        first = result.market_history[0].market_state.price
        last = result.market_history[-1].market_state.price
        total_return = last / first - 1.0
        avg_herd = sum(item.herd_index for item in result.market_history) / len(result.market_history)
        bubble_events = sum(1 for item in result.market_history if item.bubble_crash_signal)
        print("\n" + "=" * 60)
        print("📈 涌现指标:")
        print("=" * 60)
        print(f"  市场指数: {result.market_symbol}")
        print(f"  价格路径: {first:.2f} -> {last:.2f} ({total_return:.2%})")
        print(f"  平均羊群指数: {avg_herd:.3f}")
        print(f"  泡沫/崩盘/抱团波动事件: {bubble_events}")

    best_agent = max(result.final_population, key=lambda agent: agent.fitness)
    print("\n" + "=" * 60)
    print("🏆 最优个体:")
    print("=" * 60)
    print(f"  {best_agent.individual_id} ({best_agent.archetype_id})")
    print(f"  fitness={best_agent.fitness:.4f} | equity={best_agent.current_equity:.2f}")
    print(f"  genome={best_agent.genome.model_dump()}")

    print("\n" + "=" * 60)
    print("📋 涌现与进化报告:")
    print("=" * 60)
    print(result.report)


def main():
    args = parse_args()
    if args.events_file:
        news = Path(args.events_file).read_text(encoding="utf-8")
        print(f"[从事件串文件读取输入] {args.events_file}\n")
    elif args.news is None:
        news = "美联储宣布加息50基点，超出市场预期的25基点"
        print(f"[未提供消息，使用默认] {news}\n")
    else:
        news = args.news

    agent_configs = discover_agents()
    print(f"已发现 {len(agent_configs)} 个 Agent: {list(agent_configs.keys())}\n")

    if args.mode == "evolve":
        run_evolve(news, agent_configs, args)
    else:
        run_single(news, agent_configs)


if __name__ == "__main__":
    main()
