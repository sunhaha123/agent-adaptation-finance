from src.schemas.evolution import EvolutionSimulationResult
from src.simulation.events import format_event_timeline


def summarize_result(result: EvolutionSimulationResult) -> dict:
    first_price = result.market_history[0].market_state.price if result.market_history else 100.0
    last_price = result.market_history[-1].market_state.price if result.market_history else first_price
    total_return = last_price / first_price - 1.0 if first_price else 0.0
    avg_herd = (
        sum(round_snapshot.herd_index for round_snapshot in result.market_history)
        / len(result.market_history)
        if result.market_history
        else 0.0
    )
    max_vol = max((round_snapshot.market_state.volatility for round_snapshot in result.market_history), default=0.0)
    total_volume = sum(round_snapshot.market_state.volume for round_snapshot in result.market_history)
    best_agent = max(result.final_population, key=lambda agent: agent.fitness, default=None)
    return {
        "market_symbol": result.market_symbol,
        "rounds": len(result.market_history),
        "generations": len(result.generation_summaries),
        "first_price": first_price,
        "last_price": last_price,
        "total_return": total_return,
        "avg_herd_index": avg_herd,
        "max_volatility": max_vol,
        "total_volume": total_volume,
        "best_agent": best_agent.model_dump() if best_agent else None,
        "event_timeline": [event.model_dump() for event in result.event_timeline],
        "generation_summaries": [summary.model_dump() for summary in result.generation_summaries],
    }


def deterministic_report(result: EvolutionSimulationResult) -> str:
    summary = summarize_result(result)
    best = summary["best_agent"] or {}
    direction = "上涨" if summary["total_return"] > 0 else "下跌" if summary["total_return"] < 0 else "横盘"
    return (
        "## 多 Agent 涌现仿真报告\n\n"
        "### 事件串\n\n"
        f"{format_event_timeline(result.event_timeline)}\n\n"
        f"- 市场指数: {summary['market_symbol']}\n"
        f"- 轮数/代数: {summary['rounds']} / {summary['generations']}\n"
        f"- 价格路径: {summary['first_price']:.2f} -> {summary['last_price']:.2f}，整体{direction} "
        f"({summary['total_return']:.2%})\n"
        f"- 平均羊群指数: {summary['avg_herd_index']:.3f}\n"
        f"- 最大波动率: {summary['max_volatility']:.3f}\n"
        f"- 总成交量: {summary['total_volume']:.2f}\n"
        f"- 事件链节点数: {len(summary['event_timeline'])}\n"
        f"- 最优个体: {best.get('individual_id', 'N/A')}，fitness={best.get('fitness', 0.0):.4f}\n\n"
        "解释：本轮仿真中，LLM 先把初始新闻扩展为事件链，并生成群体原型信号；真实交易由 genome 参数、价格反馈、"
        "羊群传染和订单簿撮合共同驱动。遗传算法保留高 fitness 个体，使风险偏好、"
        "信号敏感度、羊群系数和逆向倾向在代际之间发生选择与变异。"
    )


def generate_emergence_report(raw_news: str, result: EvolutionSimulationResult) -> str:
    summary = summarize_result(result)
    messages = [
        {"role": "system", "content": (
            "你是一个基于 agent 的计算金融研究助理。根据结构化仿真结果生成中文报告，"
            "重点解释多 Agent 涌现、价格反馈、行为模仿、遗传算法，以及它们与论文中"
            "感知、目标、偏好、操作、反馈学习和进化机制的对应关系。"
            "报告开头必须先用“事件串”小节逐条列出事件链，格式为“阶段标题：事件描述”。"
        )},
        {"role": "user", "content": (
            f"原始新闻: {raw_news}\n\n"
            f"仿真摘要:\n{summary}"
        )},
    ]
    try:
        from src.agent_runtime.llm import get_llm

        llm = get_llm(temperature=0.2)
        response = llm.invoke(messages)
        return response.content
    except Exception as exc:
        return deterministic_report(result) + f"\n\n[LLM 报告生成失败，已使用确定性报告兜底: {type(exc).__name__}]"
