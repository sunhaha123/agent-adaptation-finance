import random

import pytest

from src.simulation.engine import run_evolution_simulation
from src.simulation.events import fallback_event_timeline
from src.simulation.population import MARKET_STRUCTURE, initialize_population, population_weights


def _war_news_signal():
    return {
        "raw_text": "美国与伊朗关系恶化，霍尔木兹海峡面临封锁风险",
        "direction": "bearish",
        "intensity": 0.9,
        "confidence": 0.9,
        "affected_assets": ["oil", "shipping", "gold", "USD", "equities", "bonds"],
        "summary": "美伊战争爆发",
    }


def _war_archetype_responses():
    return {
        "macro_fund": {"agent_id": "macro_fund", "stance": "bearish", "confidence": 0.8, "intensity": 0.7},
        "mutual_fund": {"agent_id": "mutual_fund", "stance": "neutral", "confidence": 0.6, "intensity": 0.3},
        "passive_fund": {"agent_id": "passive_fund", "stance": "neutral", "confidence": 0.8, "intensity": 0.1},
        "quant_fund": {"agent_id": "quant_fund", "stance": "bearish", "confidence": 0.8, "intensity": 0.7},
        "retail_contrarian": {"agent_id": "retail_contrarian", "stance": "bullish", "confidence": 0.6, "intensity": 0.5},
        "retail_momentum": {"agent_id": "retail_momentum", "stance": "bearish", "confidence": 0.9, "intensity": 0.9},
    }


def test_population_weights_reflect_market_structure():
    archetype_ids = sorted(MARKET_STRUCTURE.keys())
    rng = random.Random(42)
    pop = initialize_population(archetype_ids, 120, 100.0, rng)
    weights = population_weights(pop)

    for arch_id, config in MARKET_STRUCTURE.items():
        target = config["capital_weight"]
        actual = weights.get(arch_id, 0.0)
        assert abs(actual - target) < 0.05, (
            f"{arch_id}: expected ~{target:.2%}, got {actual:.2%}"
        )


@pytest.mark.slow
def test_simulation_produces_v_shaped_trajectory():
    news = _war_news_signal()
    timeline = fallback_event_timeline(news["raw_text"], news, event_count=12, total_rounds=1000)
    result = run_evolution_simulation(
        news_signal=news,
        archetype_responses=_war_archetype_responses(),
        event_timeline=timeline,
        population_size=120,
        rounds_per_generation=50,
        generations=20,
        seed=42,
    )

    prices = [snap.market_state.price for snap in result.market_history]
    initial = prices[0]
    trough = min(prices)
    final = prices[-1]

    sim_drawdown = (trough - initial) / initial
    sim_recovery = (final - trough) / trough if trough > 0 else 0
    avg_herd = sum(s.herd_index for s in result.market_history) / len(result.market_history)
    zero_vol_gens = sum(1 for g in result.generation_summaries if g.total_volume < 1e-6)

    assert sim_drawdown < -0.03, f"Expected drawdown < -3%, got {sim_drawdown:.2%}"
    assert sim_recovery > 0.02, f"Expected recovery > 2%, got {sim_recovery:.2%}"
    assert avg_herd < 0.70, f"Average herd index {avg_herd:.3f} too high"
    assert zero_vol_gens <= 2, f"Too many zero-volume generations: {zero_vol_gens}"
