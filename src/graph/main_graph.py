from langgraph.graph import StateGraph, START, END

from src.graph.state import SimulationState
from src.graph.nodes.extract_signal import extract_signal
from src.graph.nodes.dispatch_agents import dispatch_agents
from src.graph.nodes.collect_responses import agent_node
from src.graph.nodes.generate_report import generate_report


def build_graph():
    """构建主仿真图：4 个节点，无循环"""
    builder = StateGraph(SimulationState)

    builder.add_node("extract_signal", extract_signal)
    builder.add_node("agent_node", agent_node)
    builder.add_node("generate_report", generate_report)

    builder.add_edge(START, "extract_signal")
    builder.add_conditional_edges("extract_signal", dispatch_agents, ["agent_node"])
    builder.add_edge("agent_node", "generate_report")
    builder.add_edge("generate_report", END)

    return builder.compile()


# langgraph dev 需要的模块级变量
graph = build_graph()


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    news = "美联储宣布加息50基点，超出市场预期的25基点"
    print(f"测试消息: {news}\n")

    try:
        result = graph.invoke({"raw_news": news})
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        sys.exit(1)

    # 验证 news_signal
    signal = result.get("news_signal")
    if not signal:
        print("[ERROR] news_signal 为空")
        sys.exit(1)
    print(f"[OK] 信号提取: direction={signal['direction']}, intensity={signal['intensity']}")

    # 验证 responses
    responses = result.get("responses", [])
    if not responses:
        print("[ERROR] responses 为空，没有 Agent 响应")
        sys.exit(1)
    for r in responses:
        print(f"[OK] {r['agent_name']}: stance={r['stance']}, confidence={r['confidence']}")

    # 验证 report
    report = result.get("report")
    if not report:
        print("[ERROR] report 为空")
        sys.exit(1)
    print(f"[OK] 报告生成成功 ({len(report)} 字)")

    # 打印完整结果
    print("\n" + "=" * 60)
    print("信号提取:")
    print(f"  方向: {signal['direction']} | 强度: {signal['intensity']} | 置信度: {signal['confidence']}")
    print(f"  受影响资产: {', '.join(signal['affected_assets'])}")
    print(f"  摘要: {signal['summary']}")

    print("\n" + "=" * 60)
    print("各群体决策意向:")
    print("=" * 60)
    for r in responses:
        stance_map = {"bullish": "看多", "bearish": "看空", "neutral": "中性"}
        print(f"\n【{r['agent_name']}】 {stance_map.get(r['stance'], r['stance'])} | 置信度: {r['confidence']} | 强度: {r['intensity']}")
        print(f"  操作: {r['action']}")
        print(f"  推理: {r['reasoning']}")
        print(f"  时间: {r['time_horizon']} | 资产: {', '.join(r['affected_assets'])}")

    print("\n" + "=" * 60)
    print("综合分析报告:")
    print("=" * 60)
    print(report)
