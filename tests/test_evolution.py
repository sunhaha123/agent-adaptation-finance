import random

from src.schemas.evolution import AgentGenome, MarketState, Order, SocialState
from src.simulation.events import fallback_event_timeline, format_event_timeline, parse_user_event_timeline
from src.simulation.engine import run_evolution_simulation
from src.simulation.feedback import calculate_fitness
from src.simulation.genetics import evolve_population
from src.simulation.order_book import match_order_book
from src.simulation.policy import compute_order_intent
from src.simulation.population import initialize_population, make_agent, mutate_genome


def sample_news_signal(direction: str = "bullish") -> dict:
    return {
        "raw_text": "测试新闻",
        "direction": direction,
        "intensity": 0.9,
        "confidence": 0.9,
        "affected_assets": ["MARKET_INDEX"],
        "summary": "测试摘要",
    }


def sample_archetype_responses() -> dict[str, dict]:
    return {
        "macro_fund": {
            "agent_id": "macro_fund",
            "agent_name": "宏观对冲基金",
            "stance": "bullish",
            "confidence": 0.7,
            "intensity": 0.6,
        },
        "mutual_fund": {
            "agent_id": "mutual_fund",
            "agent_name": "公募/长线机构",
            "stance": "neutral",
            "confidence": 0.6,
            "intensity": 0.3,
        },
        "passive_fund": {
            "agent_id": "passive_fund",
            "agent_name": "被动资金/ETF",
            "stance": "neutral",
            "confidence": 0.8,
            "intensity": 0.1,
        },
        "quant_fund": {
            "agent_id": "quant_fund",
            "agent_name": "量化趋势基金",
            "stance": "bullish",
            "confidence": 0.8,
            "intensity": 0.7,
        },
        "retail_contrarian": {
            "agent_id": "retail_contrarian",
            "agent_name": "散户-逆向博弈",
            "stance": "bearish",
            "confidence": 0.7,
            "intensity": 0.6,
        },
        "retail_momentum": {
            "agent_id": "retail_momentum",
            "agent_name": "散户-动量追随",
            "stance": "bullish",
            "confidence": 0.95,
            "intensity": 0.9,
        },
    }


def test_genome_initialization_and_mutation_stay_in_bounds():
    rng = random.Random(42)
    population = initialize_population(["retail_momentum", "passive_fund"], 10, 100.0, rng)

    for agent in population:
        genome = agent.genome
        mutated = mutate_genome(genome, rng, mutation_rate=1.0, sigma=0.5)
        for value in mutated.model_dump().values():
            assert 0.0 <= value <= 1.0


def test_order_book_uses_price_priority_and_midpoint_price():
    previous = MarketState(
        round_index=0,
        price=100.0,
        volume=0.0,
        volatility=0.0,
        return_rate=0.0,
        order_imbalance=0.0,
    )
    orders = [
        Order(individual_id="b2", side="buy", quantity=2.0, limit_price=103.0, intent=0.5),
        Order(individual_id="b1", side="buy", quantity=1.0, limit_price=105.0, intent=0.8),
        Order(individual_id="s2", side="sell", quantity=2.0, limit_price=102.0, intent=-0.5),
        Order(individual_id="s1", side="sell", quantity=1.0, limit_price=99.0, intent=-0.8),
    ]

    trades, next_market = match_order_book(orders, previous)

    assert trades[0].buyer_id == "b1"
    assert trades[0].seller_id == "s1"
    assert trades[0].price == 102.0
    assert next_market.price > 0


def test_order_book_keeps_price_when_no_trade_and_records_liquidity_stress():
    previous = MarketState(
        round_index=0,
        price=100.0,
        volume=0.0,
        volatility=0.0,
        return_rate=0.0,
        order_imbalance=0.0,
    )
    orders = [
        Order(individual_id=f"b{i}", side="buy", quantity=100.0, limit_price=300.0, intent=1.0)
        for i in range(5)
    ]

    _, next_market = match_order_book(orders, previous, max_move=0.10)

    assert next_market.price == 100.0
    assert next_market.return_rate == 0.0
    assert next_market.liquidity_stress == 1.0


def test_fallback_event_timeline_distributes_rounds():
    events = fallback_event_timeline(
        "美联储宣布加息50基点",
        sample_news_signal("bearish"),
        event_count=4,
        total_rounds=10,
    )

    assert len(events) == 4
    assert sum(event.rounds for event in events) == 10
    assert events[0].direction == "bearish"
    assert any(event.direction == "neutral" for event in events)


def test_geopolitical_fallback_outputs_readable_event_chain():
    events = fallback_event_timeline(
        "美国与伊朗关系恶化，霍尔木兹海峡面临封锁风险",
        sample_news_signal("bearish"),
        event_count=6,
        total_rounds=12,
    )
    rendered = format_event_timeline(events)

    assert events[0].title == "前期对抗升级"
    assert "霍尔木兹风险冲击" in rendered
    assert "：" in rendered
    assert sum(event.rounds for event in events) == 12


def test_user_event_timeline_input_is_parsed_in_order():
    raw_events = """
    前期对抗升级：美伊关系恶化，地区驻军、舰队与防空力量加强部署，市场开始计入中东地缘风险溢价。
    战争爆发：美国与以色列对伊朗关键军事/核相关/指挥目标实施打击，冲突从威慑转为公开战争。
    停火窗口出现：在多方调停下，双方接受临时停火或降烈度安排，市场开始交易“最坏情形避免”。
    """
    events = parse_user_event_timeline(raw_events, total_rounds=9)

    assert [event.title for event in events] == ["前期对抗升级", "战争爆发", "停火窗口出现"]
    assert [event.direction for event in events] == ["bearish", "bearish", "bullish"]
    assert sum(event.rounds for event in events) == 9


def test_simulation_is_reproducible_with_same_seed():
    first = run_evolution_simulation(
        sample_news_signal(),
        sample_archetype_responses(),
        population_size=12,
        rounds_per_generation=5,
        generations=2,
        seed=7,
    )
    second = run_evolution_simulation(
        sample_news_signal(),
        sample_archetype_responses(),
        population_size=12,
        rounds_per_generation=5,
        generations=2,
        seed=7,
    )

    first_prices = [round(item.market_state.price, 8) for item in first.market_history]
    second_prices = [round(item.market_state.price, 8) for item in second.market_history]
    assert first_prices == second_prices


def test_integration_generates_history_population_and_summary():
    result = run_evolution_simulation(
        sample_news_signal(),
        sample_archetype_responses(),
        population_size=12,
        rounds_per_generation=5,
        generations=2,
        seed=42,
    )

    assert len(result.market_history) == 10
    assert len(result.generation_summaries) == 2
    assert len(result.final_population) == 12
    assert any(item.trades for item in result.market_history)


def test_bullish_news_pushes_momentum_agents_to_buy_early():
    result = run_evolution_simulation(
        sample_news_signal("bullish"),
        sample_archetype_responses(),
        population_size=12,
        rounds_per_generation=2,
        generations=1,
        seed=11,
    )
    first_round_orders = result.market_history[0].orders
    momentum_orders = [
        order for order in first_round_orders if order.individual_id.startswith("retail_momentum")
    ]

    assert momentum_orders
    assert all(order.side == "buy" for order in momentum_orders)


def test_herd_coefficient_amplifies_social_majority_signal():
    market = MarketState(
        round_index=0,
        price=100.0,
        volume=0.0,
        volatility=0.0,
        return_rate=0.0,
        order_imbalance=0.0,
    )
    social = SocialState(majority_action=1.0, herd_index=1.0)
    response = {"stance": "neutral", "confidence": 0.5, "intensity": 0.5}
    news = sample_news_signal("neutral")
    low_herd = make_agent(
        "low",
        "retail_momentum",
        AgentGenome(
            risk_appetite=0.5,
            signal_sensitivity=0.5,
            herd_coefficient=0.0,
            contrarian_bias=0.0,
            confidence_threshold=0.1,
            position_limit=0.5,
        ),
        100.0,
    )
    high_herd = make_agent(
        "high",
        "retail_momentum",
        AgentGenome(
            risk_appetite=0.5,
            signal_sensitivity=0.5,
            herd_coefficient=0.9,
            contrarian_bias=0.0,
            confidence_threshold=0.1,
            position_limit=0.5,
        ),
        100.0,
    )

    assert compute_order_intent(high_herd, response, news, market, social) > compute_order_intent(
        low_herd, response, news, market, social
    )


def test_fitness_penalizes_excess_position_concentration():
    genome = AgentGenome(
        risk_appetite=0.5,
        signal_sensitivity=0.5,
        herd_coefficient=0.2,
        contrarian_bias=0.2,
        confidence_threshold=0.2,
        position_limit=0.1,
    )
    concentrated = make_agent("concentrated", "macro_fund", genome, 100.0)
    concentrated.position = 100.0
    concentrated.current_equity = 11000.0

    disciplined = make_agent("disciplined", "macro_fund", genome, 100.0)
    disciplined.position = 5.0
    disciplined.current_equity = 11000.0

    assert calculate_fitness(concentrated, 100.0) < calculate_fitness(disciplined, 100.0)


def test_evolution_keeps_high_fitness_elite_genome():
    rng = random.Random(3)
    population = initialize_population(["macro_fund", "quant_fund"], 10, 100.0, rng)
    champion = population[0]
    champion.genome = AgentGenome(
        risk_appetite=0.99,
        signal_sensitivity=0.99,
        herd_coefficient=0.01,
        contrarian_bias=0.01,
        confidence_threshold=0.01,
        position_limit=0.99,
    )
    champion.fitness = 1.0
    for agent in population[1:]:
        agent.fitness = -1.0

    next_population, _ = evolve_population(population, 10, 100.0, rng, generation=1)

    assert any(agent.genome.risk_appetite == 0.99 for agent in next_population)
