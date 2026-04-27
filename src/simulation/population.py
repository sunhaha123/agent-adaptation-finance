import random
from collections import Counter

from src.schemas.evolution import AgentGenome, AgentRuntimeState
from src.simulation.utils import clamp

INITIAL_EQUITY = 10000.0


MARKET_STRUCTURE: dict[str, dict[str, float]] = {
    "passive_fund":      {"capital_weight": 0.25, "min_weight": 0.12},
    "mutual_fund":       {"capital_weight": 0.25, "min_weight": 0.12},
    "retail_momentum":   {"capital_weight": 0.20, "min_weight": 0.10},
    "retail_contrarian": {"capital_weight": 0.08, "min_weight": 0.04},
    "quant_fund":        {"capital_weight": 0.12, "min_weight": 0.05},
    "macro_fund":        {"capital_weight": 0.10, "min_weight": 0.05},
}


GENOME_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "passive_fund": {
        "risk_appetite": (0.03, 0.15),
        "signal_sensitivity": (0.03, 0.12),
        "herd_coefficient": (0.00, 0.10),
        "contrarian_bias": (0.00, 0.05),
        "confidence_threshold": (0.70, 0.92),
        "position_limit": (0.03, 0.12),
    },
    "retail_momentum": {
        "risk_appetite": (0.50, 0.90),
        "signal_sensitivity": (0.55, 0.92),
        "herd_coefficient": (0.55, 0.92),
        "contrarian_bias": (0.00, 0.12),
        "confidence_threshold": (0.10, 0.35),
        "position_limit": (0.25, 0.85),
    },
    "retail_contrarian": {
        "risk_appetite": (0.25, 0.55),
        "signal_sensitivity": (0.20, 0.50),
        "herd_coefficient": (0.03, 0.20),
        "contrarian_bias": (0.60, 0.95),
        "confidence_threshold": (0.15, 0.40),
        "position_limit": (0.10, 0.45),
    },
    "quant_fund": {
        "risk_appetite": (0.30, 0.55),
        "signal_sensitivity": (0.55, 0.90),
        "herd_coefficient": (0.15, 0.40),
        "contrarian_bias": (0.05, 0.25),
        "confidence_threshold": (0.20, 0.45),
        "position_limit": (0.15, 0.50),
    },
    "mutual_fund": {
        "risk_appetite": (0.18, 0.42),
        "signal_sensitivity": (0.18, 0.45),
        "herd_coefficient": (0.08, 0.28),
        "contrarian_bias": (0.10, 0.35),
        "confidence_threshold": (0.45, 0.75),
        "position_limit": (0.12, 0.35),
    },
    "macro_fund": {
        "risk_appetite": (0.50, 0.80),
        "signal_sensitivity": (0.50, 0.85),
        "herd_coefficient": (0.03, 0.20),
        "contrarian_bias": (0.30, 0.70),
        "confidence_threshold": (0.20, 0.50),
        "position_limit": (0.30, 0.75),
    },
}

DEFAULT_GENOME_RANGE = {
    "risk_appetite": (0.20, 0.70),
    "signal_sensitivity": (0.20, 0.80),
    "herd_coefficient": (0.05, 0.60),
    "contrarian_bias": (0.05, 0.60),
    "confidence_threshold": (0.20, 0.70),
    "position_limit": (0.15, 0.65),
}


def random_genome(archetype_id: str, rng: random.Random) -> AgentGenome:
    ranges = GENOME_RANGES.get(archetype_id, DEFAULT_GENOME_RANGE)
    values = {name: rng.uniform(low, high) for name, (low, high) in ranges.items()}
    return AgentGenome(**values)


def make_agent(
    individual_id: str,
    archetype_id: str,
    genome: AgentGenome,
    initial_price: float,
    initial_equity: float = INITIAL_EQUITY,
) -> AgentRuntimeState:
    initial_position_value = initial_equity * 0.5
    position = initial_position_value / initial_price
    cash = initial_equity - initial_position_value
    return AgentRuntimeState(
        individual_id=individual_id,
        archetype_id=archetype_id,
        genome=genome,
        cash=cash,
        position=position,
        initial_equity=initial_equity,
        current_equity=initial_equity,
        peak_equity=initial_equity,
    )


def initialize_population(
    archetype_ids: list[str],
    population_size: int,
    initial_price: float,
    rng: random.Random,
    market_structure: dict[str, dict[str, float]] | None = None,
) -> list[AgentRuntimeState]:
    if not archetype_ids:
        raise ValueError("至少需要一个 agent 原型才能初始化 population")
    if population_size < len(archetype_ids):
        raise ValueError("population_size 不能小于 agent 原型数量")

    structure = market_structure or MARKET_STRUCTURE
    raw = [structure.get(aid, {}).get("capital_weight", 1.0 / len(archetype_ids)) for aid in archetype_ids]
    total = sum(raw) or 1.0
    normalized = [w / total for w in raw]

    counts = [max(1, int(n * population_size)) for n in normalized]
    remainders = sorted(
        ((n * population_size - counts[i], i) for i, n in enumerate(normalized)),
        reverse=True,
    )
    while sum(counts) < population_size:
        for _, i in remainders:
            if sum(counts) >= population_size:
                break
            counts[i] += 1
    while sum(counts) > population_size:
        for _, i in reversed(remainders):
            if sum(counts) <= population_size:
                break
            if counts[i] > 1:
                counts[i] -= 1

    population: list[AgentRuntimeState] = []
    for arch_idx, archetype_id in enumerate(archetype_ids):
        for _ in range(counts[arch_idx]):
            genome = random_genome(archetype_id, rng)
            individual_id = f"{archetype_id}_{len(population):03d}"
            population.append(make_agent(individual_id, archetype_id, genome, initial_price))
    return population


def clone_for_next_generation(
    agent: AgentRuntimeState,
    individual_id: str,
    initial_price: float,
) -> AgentRuntimeState:
    return make_agent(individual_id, agent.archetype_id, agent.genome.model_copy(), initial_price)


def mutate_genome(
    genome: AgentGenome,
    rng: random.Random,
    mutation_rate: float = 0.12,
    sigma: float = 0.07,
) -> AgentGenome:
    values = genome.model_dump()
    for name, value in values.items():
        if rng.random() < mutation_rate:
            values[name] = clamp(value + rng.gauss(0.0, sigma), 0.0, 1.0)
    return AgentGenome(**values)


def crossover_genomes(parent_a: AgentGenome, parent_b: AgentGenome, rng: random.Random) -> AgentGenome:
    alpha = rng.random()
    values = {}
    for name in AgentGenome.model_fields:
        a = getattr(parent_a, name)
        b = getattr(parent_b, name)
        values[name] = clamp(alpha * a + (1 - alpha) * b, 0.0, 1.0)
    return AgentGenome(**values)


def population_weights(population: list[AgentRuntimeState]) -> dict[str, float]:
    counts = Counter(agent.archetype_id for agent in population)
    total = sum(counts.values()) or 1
    return {key: value / total for key, value in sorted(counts.items())}
