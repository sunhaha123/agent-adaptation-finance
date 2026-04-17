import re
import yaml
from src.schemas.response import AgentResponse
from src.agent_runtime.llm import llm_with_json_output


def load_agent_config(md_path: str) -> dict:
    """从 .md 文件加载 agent 配置，解析 frontmatter + body"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid agent config format: {md_path}")

    meta = yaml.safe_load(match.group(1))
    body = match.group(2).strip()

    return {
        "agent_id": meta["agent_id"],
        "agent_name": meta["agent_name"],
        "system_prompt": body,
    }


def run_agent(agent_config: dict, news_signal: dict) -> dict:
    """运行单个 Agent，输入新闻信号，输出结构化决策意向"""
    system_prompt = agent_config["system_prompt"]
    agent_id = agent_config["agent_id"]
    agent_name = agent_config["agent_name"]

    news_text = (
        f"新闻原文：{news_signal['raw_text']}\n"
        f"信号方向：{news_signal['direction']}\n"
        f"信号强度：{news_signal['intensity']}\n"
        f"置信度：{news_signal['confidence']}\n"
        f"受影响资产：{', '.join(news_signal['affected_assets'])}\n"
        f"摘要：{news_signal['summary']}"
    )

    messages = [
        {"role": "system", "content": (
            f"{system_prompt}\n\n"
            f"你的 agent_id 是 \"{agent_id}\"，agent_name 是 \"{agent_name}\"。\n"
            f"请严格按照要求输出你的决策意向。"
        )},
        {"role": "user", "content": f"请对以下市场消息做出你的决策反应：\n\n{news_text}"},
    ]

    response = llm_with_json_output(messages, AgentResponse)
    return response.model_dump()
