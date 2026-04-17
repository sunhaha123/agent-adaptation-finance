from pydantic import BaseModel, Field
from typing import Literal


class NewsSignal(BaseModel):
    raw_text: str = Field(description="原始新闻文本")
    direction: Literal["bullish", "bearish", "neutral"] = Field(description="市场方向：利多/利空/中性")
    intensity: float = Field(ge=0, le=1, description="信号强度 0-1")
    confidence: float = Field(ge=0, le=1, description="置信度 0-1")
    affected_assets: list[str] = Field(description="受影响的资产类别")
    summary: str = Field(description="一句话摘要")


class AgentResponse(BaseModel):
    agent_id: str = Field(description="Agent 标识")
    agent_name: str = Field(description="Agent 名称")
    stance: Literal["bullish", "bearish", "neutral"] = Field(description="立场：看多/看空/中性")
    confidence: float = Field(ge=0, le=1, description="置信度 0-1")
    intensity: float = Field(ge=0, le=1, description="行动强度 0-1")
    action: str = Field(description="具体建议操作")
    reasoning: str = Field(description="推理过程")
    time_horizon: str = Field(description="时间视角")
    affected_assets: list[str] = Field(description="受影响的资产类别")
