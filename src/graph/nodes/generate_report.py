from src.graph.state import SimulationState
from src.agent_runtime.llm import get_llm


def generate_report(state: SimulationState) -> dict:
    """汇总所有 Agent 的决策意向，生成对比分析报告"""
    llm = get_llm(temperature=0.3)

    responses_text = ""
    for r in state["responses"]:
        responses_text += (
            f"\n### {r['agent_name']} ({r['agent_id']})\n"
            f"- 立场: {r['stance']}\n"
            f"- 置信度: {r['confidence']}\n"
            f"- 行动强度: {r['intensity']}\n"
            f"- 操作建议: {r['action']}\n"
            f"- 推理: {r['reasoning']}\n"
            f"- 时间视角: {r['time_horizon']}\n"
            f"- 受影响资产: {', '.join(r['affected_assets'])}\n"
        )

    messages = [
        {"role": "system", "content": (
            "你是一个金融市场分析师。根据不同交易群体对同一条消息的反应，"
            "生成一份对比分析报告。重点分析：\n"
            "1. 各群体反应的异同\n"
            "2. 分歧最大的地方在哪里\n"
            "3. 综合来看市场可能的走向\n"
            "4. 哪些群体的判断可能更准确\n"
            "用中文输出，简洁专业。"
        )},
        {"role": "user", "content": (
            f"原始消息: {state['raw_news']}\n\n"
            f"各群体反应如下:\n{responses_text}"
        )},
    ]

    result = llm.invoke(messages)
    return {"report": result.content}
