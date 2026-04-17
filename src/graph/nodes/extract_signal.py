from src.schemas.response import NewsSignal
from src.graph.state import SimulationState
from src.agent_runtime.llm import llm_with_json_output


def extract_signal(state: SimulationState) -> dict:
    """将原始新闻文本结构化为 NewsSignal"""
    messages = [
        {"role": "system", "content": (
            "你是一个金融新闻分析师。将用户提供的新闻消息结构化为标准的市场信号格式。\n"
            "- raw_text: 保留原始文本\n"
            "- direction: 判断该消息对市场整体是利多(bullish)、利空(bearish)还是中性(neutral)\n"
            "- intensity: 信号强度 0-1，重大事件接近1\n"
            "- confidence: 你对判断的置信度 0-1\n"
            "- affected_assets: 列出受影响的资产类别\n"
            "- summary: 一句话总结"
        )},
        {"role": "user", "content": state["raw_news"]},
    ]

    signal = llm_with_json_output(messages, NewsSignal, temperature=0)
    return {"news_signal": signal.model_dump()}
