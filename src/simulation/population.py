import random
from collections import Counter

from src.schemas.evolution import AgentGenome, AgentRuntimeState
from src.simulation.utils import clamp

INITIAL_EQUITY = 10000.0


GENOME_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "passive_fund": {
        "risk_appetite": (0.05, 0.20),
        "signal_sensitivity": (0.05, 0.20),
        "herd_coefficient": (0.00, 0.15),
        "contrarian_bias": (0.00, 0.10),
        "confidence_threshold": (0.65, 0.90),
        "position_limit": (0.05, 0.15),
    },
    "retail_momentum": {
        "risk_appetite": (0.50, 0.90),
        "signal_sensitivity": (0.50, 0.90),
        "herd_coefficient": (0.55, 0.95),
        "contrarian_bias": (0.00, 0.15),
        "confidence_threshold": (0.10, 0.40),
        "position_limit": (0.25, 0.80),
    },
    "retail_contrarian": {
        "risk_appetite": (0.30, 0.65),
        "signal_sensitivity": (0.25, 0.60),
        "herd_coefficient": (0.05, 0.35),
        "contrarian_bias": (0.55, 0.95),
        "confidence_threshold": (0.15, 0.40),
        "position_limit": (0.15, 0.55),
    },
    "quant_fund": {
        "risk_appetite": (0.35, 0.65),
        "signal_sensitivity": (0.45, 0.85),
        "herd_coefficient": (0.10, 0.35),
        "contrarian_bias": (0.10, 0.35),
        "confidence_threshold": (0.30, 0.60),
        "position_limit": (0.20, 0.60),
    },
    "mutual_fund": {
        "risk_appetite": (0.20, 0.45),
        "signal_sensitivity": (0.25, 0.55),
        "herd_coefficient": (0.05, 0.25),
        "contrarian_bias": (0.10, 0.35),
        "confidence_threshold": (0.45, 0.75),
        "position_limit": (0.15, 0.40),
    },
    "macro_fund": {
        "risk_appetite": (0.45, 0.75),
        "signal_sensitivity": (0.45, 0.85),
        "herd_coefficient": (0.05, 0.25),
        "contrarian_bias": (0.25, 0.65),
        "confidence_threshold": (0.25, 0.55),
        "position_limit": (0.25, 0.70),
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
) -> list[AgentRuntimeState]:
    if not archetype_ids:
        raise ValueError("至少需要一个 agent 原型才能初始化 population")
    if population_size < len(archetype_ids):
        raise ValueError("population_size 不能小于 agent 原型数量")

    population: list[AgentRuntimeState] = []
    for index in range(population_size):
        archetype_id = archetype_ids[index % len(archetype_ids)]
        genome = random_genome(archetype_id, rng)
        individual_id = f"{archetype_id}_{index:03d}"
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
