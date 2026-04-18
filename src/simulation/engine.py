import random

from src.schemas.evolution import (
    EvolutionSimulationResult,
    GenerationSummary,
    MarketEvent,
    MarketState,
    RoundSnapshot,
    SocialState,
)
from src.simulation.events import (
    adapt_archetype_response,
    build_event_schedule,
    event_to_signal,
    fallback_event_timeline,
    generate_event_timeline,
)
from src.simulation.feedback import apply_trades, build_social_state, update_population_after_market
from src.simulation.genetics import evolve_population, group_average_fitness
from src.simulation.order_book import match_order_book
from src.simulation.policy import generate_order
from src.simulation.population import initialize_population, population_weights
from src.simulation.reporting import generate_emergence_report
from src.simulation.utils import mean

MARKET_SYMBOL = "MARKET_INDEX"
INITIAL_PRICE = 100.0


def generate_archetype_signals(agent_configs: dict[str, str], news_signal: dict) -> dict[str, dict]:
    from src.agent_runtime.agent_factory import load_agent_config, run_agent

    responses = {}
    for agent_id, md_path in agent_configs.items():
        config = load_agent_config(md_path)
        response = run_agent(config, news_signal)
        responses[agent_id] = response
    return responses


def detect_bubble_or_crash(
    return_rate: float,
    volatility: float,
    herd_index: float,
    liquidity_stress: float,
) -> str | None:
    if return_rate > 0.05 and herd_index > 0.70:
        return "bubble"
    if return_rate < -0.05 and herd_index > 0.70:
        return "crash"
    if liquidity_stress > 0.80 and herd_index > 0.80:
        return "liquidity_freeze"
    if volatility > 0.04 and herd_index > 0.80:
        return "herding_volatility"
    return None


def run_evolution_simulation(
    news_signal: dict,
    archetype_responses: dict[str, dict],
    event_timeline: list[MarketEvent] | None = None,
    population_size: int = 120,
    rounds_per_generation: int = 50,
    generations: int = 20,
    seed: int = 42,
    initial_price: float = INITIAL_PRICE,
) -> EvolutionSimulationResult:
    if population_size <= 0:
        raise ValueError("population_size 必须大于 0")
    if rounds_per_generation <= 0:
        raise ValueError("rounds_per_generation 必须大于 0")
    if generations <= 0:
        raise ValueError("generations 必须大于 0")

    rng = random.Random(seed)
    total_rounds = rounds_per_generation * generations
    if event_timeline is None:
        event_timeline = fallback_event_timeline(
            news_signal.get("raw_text", ""),
            news_signal,
            event_count=1,
            total_rounds=total_rounds,
        )
    event_schedule = build_event_schedule(event_timeline)
    if len(event_schedule) < total_rounds:
        last_event = event_timeline[-1]
        event_schedule.extend((last_event, last_event.rounds - 1) for _ in range(total_rounds - len(event_schedule)))

    archetype_ids = sorted(archetype_responses.keys())
    population = initialize_population(archetype_ids, population_size, initial_price, rng)
    market_state = MarketState(
        round_index=0,
        price=initial_price,
        volume=0.0,
        volatility=0.0,
        return_rate=0.0,
        order_imbalance=0.0,
    )
    social_state = SocialState()
    market_history: list[RoundSnapshot] = []
    generation_summaries: list[GenerationSummary] = []
    recent_returns: list[float] = []

    for generation in range(generations):
        generation_start_price = market_state.price
        generation_rounds: list[RoundSnapshot] = []

        for _ in range(rounds_per_generation):
            global_round = len(market_history)
            active_event, event_local_round = event_schedule[min(global_round, len(event_schedule) - 1)]
            event_signal = event_to_signal(active_event, event_local_round)
            orders = []
            for agent in population:
                archetype_response = adapt_archetype_response(
                    archetype_responses[agent.archetype_id],
                    event_signal,
                    agent.archetype_id,
                )
                order = generate_order(
                    agent,
                    archetype_response,
                    event_signal,
                    market_state,
                    social_state,
                    rng,
                )
                if order is not None:
                    orders.append(order)

            trades, next_market = match_order_book(orders, market_state, recent_returns)
            apply_trades(population, trades)
            update_population_after_market(population, next_market.price)
            social_state = build_social_state(population, orders)
            recent_returns.append(next_market.return_rate)
            recent_returns = recent_returns[-20:]

            buy_pressure = sum(order.quantity for order in orders if order.side == "buy")
            sell_pressure = sum(order.quantity for order in orders if order.side == "sell")
            herd_index = social_state.herd_index
            snapshot = RoundSnapshot(
                generation=generation,
                round_index=next_market.round_index,
                event=active_event,
                market_state=next_market,
                orders=orders,
                trades=trades,
                herd_index=herd_index,
                disagreement=1.0 - herd_index,
                majority_action=social_state.majority_action,
                buy_pressure=buy_pressure,
                sell_pressure=sell_pressure,
                bubble_crash_signal=detect_bubble_or_crash(
                    next_market.return_rate,
                    next_market.volatility,
                    herd_index,
                    next_market.liquidity_stress,
                ),
            )
            market_history.append(snapshot)
            generation_rounds.append(snapshot)
            market_state = next_market

        group_avg = group_average_fitness(population)
        generation_summaries.append(
            GenerationSummary(
                generation=generation,
                start_price=generation_start_price,
                end_price=market_state.price,
                best_fitness=max(agent.fitness for agent in population),
                avg_fitness=mean([agent.fitness for agent in population]),
                avg_herd_index=mean([item.herd_index for item in generation_rounds]),
                total_volume=sum(item.market_state.volume for item in generation_rounds),
                group_weights=population_weights(population),
                group_avg_fitness=group_avg,
                bubble_crash_events=sum(
                    1 for item in generation_rounds if item.bubble_crash_signal is not None
                ),
            )
        )

        if generation < generations - 1:
            population, evolved_weights = evolve_population(
                population,
                population_size,
                market_state.price,
                rng,
                generation=generation + 1,
            )
            generation_summaries[-1].group_weights = evolved_weights

    return EvolutionSimulationResult(
        market_symbol=MARKET_SYMBOL,
        news_signal=news_signal,
        event_timeline=event_timeline,
        archetype_responses=archetype_responses,
        market_history=market_history,
        generation_summaries=generation_summaries,
        final_population=population,
    )


def run_evolution_mode(
    raw_news: str,
    agent_configs: dict[str, str],
    population_size: int = 120,
    rounds_per_generation: int = 50,
    generations: int = 20,
    event_count: int = 8,
    seed: int = 42,
) -> EvolutionSimulationResult:
    from src.graph.nodes.extract_signal import extract_signal

    signal_state = extract_signal({"raw_news": raw_news})
    news_signal = signal_state["news_signal"]
    event_timeline = generate_event_timeline(
        raw_news,
        news_signal,
        event_count=event_count,
        total_rounds=rounds_per_generation * generations,
    )
    archetype_responses = generate_archetype_signals(agent_configs, news_signal)
    result = run_evolution_simulation(
        news_signal=news_signal,
        archetype_responses=archetype_responses,
        event_timeline=event_timeline,
        population_size=population_size,
        rounds_per_generation=rounds_per_generation,
        generations=generations,
        seed=seed,
    )
    result.report = generate_emergence_report(raw_news, result)
    return result
