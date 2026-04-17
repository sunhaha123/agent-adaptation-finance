import os
import glob
from langgraph.types import Send
from src.graph.state import SimulationState

AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents")


def _discover_agents() -> dict[str, str]:
    """自动发现 agents/ 目录下的所有 .md 配置"""
    agents_dir = os.path.normpath(AGENTS_DIR)
    configs = {}
    for md_path in sorted(glob.glob(os.path.join(agents_dir, "*.md"))):
        agent_id = os.path.splitext(os.path.basename(md_path))[0]
        configs[agent_id] = md_path
    return configs


def dispatch_agents(state: SimulationState) -> list[Send]:
    """并行触发所有 Agent"""
    agent_configs = state.get("agent_configs") or _discover_agents()

    sends = []
    for agent_id, md_path in agent_configs.items():
        sends.append(
            Send("agent_node", {
                "agent_id": agent_id,
                "agent_md_path": md_path,
                "news_signal": state["news_signal"],
            })
        )
    return sends
