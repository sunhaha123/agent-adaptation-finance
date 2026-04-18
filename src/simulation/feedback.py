from collections import defaultdict

from src.schemas.evolution import AgentRuntimeState, Order, SocialState, Trade
from src.simulation.utils import clamp, mean


def apply_trades(
    population: list[AgentRuntimeState],
    trades: list[Trade],
) -> None:
    agents = {agent.individual_id: agent for agent in population}
    for trade in trades:
        buyer = agents[trade.buyer_id]
        seller = agents[trade.seller_id]
        notional = trade.quantity * trade.price

        buyer.cash -= notional
        buyer.position += trade.quantity
        buyer.turnover += notional / buyer.initial_equity

        seller.cash += notional
        seller.position -= trade.quantity
        seller.turnover += notional / seller.initial_equity


def update_population_after_market(
    population: list[AgentRuntimeState],
    market_price: float,
) -> None:
    for agent in population:
        previous_equity = agent.current_equity
        current_equity = agent.cash + agent.position * market_price
        agent.current_equity = current_equity
        agent.last_pnl = current_equity - previous_equity
        agent.peak_equity = max(agent.peak_equity, current_equity)
        if agent.peak_equity > 0:
            drawdown = (agent.peak_equity - current_equity) / agent.peak_equity
            agent.max_drawdown = max(agent.max_drawdown, drawdown)
        agent.fitness = calculate_fitness(agent, market_price)


def calculate_fitness(agent: AgentRuntimeState, market_price: float) -> float:
    total_return = (agent.current_equity - agent.initial_equity) / agent.initial_equity
    drawdown_penalty = agent.max_drawdown * 0.70
    turnover_penalty = agent.turnover * 0.03
    position_value = abs(agent.position * market_price)
    concentration = position_value / agent.initial_equity
    concentration_penalty = max(0.0, concentration - agent.genome.position_limit) * 0.50
    return total_return - drawdown_penalty - turnover_penalty - concentration_penalty


def build_social_state(
    population: list[AgentRuntimeState],
    orders: list[Order],
) -> SocialState:
    buy_qty = sum(order.quantity for order in orders if order.side == "buy")
    sell_qty = sum(order.quantity for order in orders if order.side == "sell")
    total_qty = buy_qty + sell_qty
    majority_action = (buy_qty - sell_qty) / total_qty if total_qty > 0 else 0.0
    herd_index = abs(majority_action)

    top_action = "hold"
    if population:
        top_agent = max(population, key=lambda agent: agent.fitness)
        top_action = top_agent.last_action

    by_group: dict[str, list[float]] = defaultdict(list)
    for agent in population:
        by_group[agent.archetype_id].append(agent.fitness)

    return SocialState(
        majority_action=clamp(majority_action, -1.0, 1.0),
        herd_index=clamp(herd_index, 0.0, 1.0),
        top_action=top_action,
        group_average_fitness={key: mean(values) for key, values in sorted(by_group.items())},
    )
