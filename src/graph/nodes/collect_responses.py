from src.graph.state import AgentTaskState
from src.agent_runtime.agent_factory import load_agent_config, run_agent


def agent_node(state: AgentTaskState) -> dict:
    """单个 Agent 的执行节点（被 Send 调用）"""
    config = load_agent_config(state["agent_md_path"])
    response = run_agent(config, state["news_signal"])
    return {"responses": [response]}
