from typing import Literal, Optional

from pydantic import BaseModel, Field


ActionSide = Literal["buy", "sell"]
LastAction = Literal["buy", "sell", "hold"]


class AgentGenome(BaseModel):
    risk_appetite: float = Field(ge=0, le=1, description="风险偏好")
    signal_sensitivity: float = Field(ge=0, le=1, description="对新闻/LLM 信号敏感度")
    herd_coefficient: float = Field(ge=0, le=1, description="羊群系数")
    contrarian_bias: float = Field(ge=0, le=1, description="逆向倾向")
    confidence_threshold: float = Field(ge=0, le=1, description="出手阈值")
    position_limit: float = Field(ge=0, le=1, description="最大仓位")


class AgentRuntimeState(BaseModel):
    individual_id: str
    archetype_id: str
    genome: AgentGenome
    cash: float
    position: float
    fitness: float = 0.0
    last_pnl: float = 0.0
    initial_equity: float = 10000.0
    current_equity: float = 10000.0
    peak_equity: float = 10000.0
    max_drawdown: float = 0.0
    turnover: float = 0.0
    last_action: LastAction = "hold"


class MarketState(BaseModel):
    round_index: int
    price: float = Field(gt=0)
    volume: float = Field(ge=0)
    volatility: float = Field(ge=0)
    return_rate: float
    order_imbalance: float = Field(ge=-1, le=1)
    liquidity_stress: float = Field(default=0.0, ge=0, le=1)


class MarketEvent(BaseModel):
    step: int
    title: str
    description: str
    direction: Literal["bullish", "bearish", "neutral"]
    intensity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    affected_assets: list[str] = Field(default_factory=list)
    rounds: int = Field(default=1, ge=1)


class Order(BaseModel):
    individual_id: str
    side: ActionSide
    quantity: float = Field(gt=0)
    limit_price: float = Field(gt=0)
    intent: float = Field(ge=-1, le=1)


class Trade(BaseModel):
    buyer_id: str
    seller_id: str
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)


class SocialState(BaseModel):
    majority_action: float = Field(default=0.0, ge=-1, le=1)
    herd_index: float = Field(default=0.0, ge=0, le=1)
    top_action: LastAction = "hold"
    group_average_fitness: dict[str, float] = Field(default_factory=dict)


class RoundSnapshot(BaseModel):
    generation: int
    round_index: int
    event: MarketEvent | None = None
    market_state: MarketState
    orders: list[Order]
    trades: list[Trade]
    herd_index: float = Field(ge=0, le=1)
    disagreement: float = Field(ge=0, le=1)
    majority_action: float = Field(ge=-1, le=1)
    buy_pressure: float = Field(ge=0)
    sell_pressure: float = Field(ge=0)
    bubble_crash_signal: Optional[str] = None


class GenerationSummary(BaseModel):
    generation: int
    start_price: float
    end_price: float
    best_fitness: float
    avg_fitness: float
    avg_herd_index: float
    total_volume: float
    group_weights: dict[str, float]
    group_avg_fitness: dict[str, float]
    bubble_crash_events: int


class EvolutionSimulationResult(BaseModel):
    market_symbol: str
    news_signal: dict
    event_timeline: list[MarketEvent] = Field(default_factory=list)
    archetype_responses: dict[str, dict]
    market_history: list[RoundSnapshot]
    generation_summaries: list[GenerationSummary]
    final_population: list[AgentRuntimeState]
    report: Optional[str] = None
