from typing import TypedDict, Optional
from typing_extensions import Annotated
import operator

from src.schemas.response import NewsSignal, AgentResponse


class AgentTaskState(TypedDict):
    """Send() 传递给每个 Agent 节点的输入状态"""
    agent_id: str
    agent_md_path: str
    news_signal: dict


class SimulationState(TypedDict):
    raw_news: str
    news_signal: Optional[dict]
    agent_configs: Optional[dict[str, str]]  # agent_id -> .md 路径，不传则自动发现
    responses: Annotated[list[dict], operator.add]
    report: Optional[str]
