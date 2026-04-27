import random

from src.schemas.evolution import AgentRuntimeState, MarketState, Order, SocialState
from src.simulation.utils import clamp, stance_to_score


def compute_order_intent(
    agent: AgentRuntimeState,
    archetype_response: dict,
    news_signal: dict,
    market_state: MarketState,
    social_state: SocialState,
    reference_price: float | None = None,
) -> float:
    genome = agent.genome
    prototype_score = (
        stance_to_score(archetype_response.get("stance", "neutral"))
        * float(archetype_response.get("confidence", 0.5))
        * float(archetype_response.get("intensity", 0.5))
    )
    news_score = (
        stance_to_score(news_signal.get("direction", "neutral"))
        * float(news_signal.get("confidence", 0.5))
        * float(news_signal.get("intensity", 0.5))
    )
    recent_return_score = clamp(market_state.return_rate * 10.0, -1.0, 1.0)

    signal_component = 0.45 * prototype_score + 0.35 * genome.signal_sensitivity * news_score
    news_contrarian_component = -0.25 * genome.contrarian_bias * news_score

    herd_damping = max(0.05, 1.0 - social_state.herd_index ** 2)
    herd_component = 0.35 * genome.herd_coefficient * social_state.majority_action * herd_damping
    contrarian_component = -0.35 * genome.contrarian_bias * social_state.majority_action
    trend_component = recent_return_score * (
        0.25 * (1.0 - genome.contrarian_bias) - 0.15 * genome.contrarian_bias
    )

    mean_reversion_component = 0.0
    if reference_price is not None and reference_price > 0:
        price_deviation = (market_state.price - reference_price) / reference_price
        if price_deviation < 0:
            reversion_signal = -clamp(price_deviation * 3.0, -1.0, 1.0)
            reversion_weight = 0.20 + 0.25 * genome.contrarian_bias
        else:
            reversion_signal = -clamp(price_deviation * 5.0, -1.0, 1.0)
            reversion_weight = 0.30 + 0.15 * genome.contrarian_bias
        mean_reversion_component = reversion_weight * reversion_signal

    return clamp(
        signal_component
        + news_contrarian_component
        + herd_component
        + contrarian_component
        + trend_component
        + mean_reversion_component,
        -1.0,
        1.0,
    )


def generate_order(
    agent: AgentRuntimeState,
    archetype_response: dict,
    news_signal: dict,
    market_state: MarketState,
    social_state: SocialState,
    rng: random.Random,
    reference_price: float | None = None,
) -> Order | None:
    intent = compute_order_intent(agent, archetype_response, news_signal, market_state, social_state, reference_price)
    if abs(intent) < agent.genome.confidence_threshold:
        agent.last_action = "hold"
        return None

    side = "buy" if intent > 0 else "sell"
    price = market_state.price
    max_notional = agent.initial_equity * agent.genome.position_limit
    order_notional = max_notional * abs(intent) * (0.25 + 0.75 * agent.genome.risk_appetite)
    if order_notional <= 0:
        agent.last_action = "hold"
        return None

    aggressiveness = 0.002 + abs(intent) * 0.015 + agent.genome.risk_appetite * 0.005
    jitter = rng.uniform(0.0, 0.002)
    if side == "buy":
        limit_price = price * (1.0 + aggressiveness + jitter)
        affordable_quantity = agent.cash / limit_price
        quantity = min(order_notional / limit_price, affordable_quantity)
    else:
        limit_price = price * (1.0 - aggressiveness - jitter)
        quantity = min(order_notional / limit_price, max(agent.position, 0.0))

    if quantity <= 1e-8:
        agent.last_action = "hold"
        return None

    agent.last_action = side
    return Order(
        individual_id=agent.individual_id,
        side=side,
        quantity=quantity,
        limit_price=max(limit_price, 0.01),
        intent=intent,
    )
