import math
import random
from collections import defaultdict

from src.schemas.evolution import AgentRuntimeState
from src.simulation.population import (
    clone_for_next_generation,
    crossover_genomes,
    make_agent,
    mutate_genome,
    population_weights,
)
from src.simulation.utils import mean


def tournament_select(
    candidates: list[AgentRuntimeState],
    rng: random.Random,
    k: int = 3,
) -> AgentRuntimeState:
    if not candidates:
        raise ValueError("tournament_select 需要至少一个候选 agent")
    sample_size = min(k, len(candidates))
    selected = rng.sample(candidates, sample_size)
    return max(selected, key=lambda agent: agent.fitness)


def group_average_fitness(population: list[AgentRuntimeState]) -> dict[str, float]:
    by_group: dict[str, list[float]] = defaultdict(list)
    for agent in population:
        by_group[agent.archetype_id].append(agent.fitness)
    return {key: mean(values) for key, values in sorted(by_group.items())}


def evolved_group_weights(population: list[AgentRuntimeState]) -> dict[str, float]:
    base_weights = population_weights(population)
    averages = group_average_fitness(population)
    if not averages:
        return base_weights

    max_avg = max(averages.values())
    exp_scores = {key: math.exp((value - max_avg) * 5.0) for key, value in averages.items()}
    exp_total = sum(exp_scores.values()) or 1.0
    fitness_weights = {key: value / exp_total for key, value in exp_scores.items()}

    keys = sorted(base_weights.keys() | fitness_weights.keys())
    mixed = {
        key: 0.80 * base_weights.get(key, 0.0) + 0.20 * fitness_weights.get(key, 0.0)
        for key in keys
    }
    total = sum(mixed.values()) or 1.0
    return {key: value / total for key, value in mixed.items()}


def sample_group(weights: dict[str, float], rng: random.Random) -> str:
    threshold = rng.random()
    cumulative = 0.0
    last_key = next(iter(weights))
    for key, weight in weights.items():
        cumulative += weight
        last_key = key
        if threshold <= cumulative:
            return key
    return last_key


def evolve_population(
    population: list[AgentRuntimeState],
    target_size: int,
    initial_price: float,
    rng: random.Random,
    generation: int,
    elite_fraction: float = 0.10,
) -> tuple[list[AgentRuntimeState], dict[str, float]]:
    if not population:
        raise ValueError("population 不能为空")

    weights = evolved_group_weights(population)
    sorted_agents = sorted(population, key=lambda agent: agent.fitness, reverse=True)
    elite_count = max(1, min(target_size, int(target_size * elite_fraction)))

    next_population: list[AgentRuntimeState] = []
    for index, elite in enumerate(sorted_agents[:elite_count]):
        individual_id = f"g{generation}_{elite.archetype_id}_elite_{index:03d}"
        next_population.append(clone_for_next_generation(elite, individual_id, initial_price))

    by_group: dict[str, list[AgentRuntimeState]] = defaultdict(list)
    for agent in population:
        by_group[agent.archetype_id].append(agent)

    while len(next_population) < target_size:
        archetype_id = sample_group(weights, rng)
        candidates = by_group.get(archetype_id) or population
        parent_a = tournament_select(candidates, rng)
        parent_b = tournament_select(candidates, rng)
        child_genome = crossover_genomes(parent_a.genome, parent_b.genome, rng)
        child_genome = mutate_genome(child_genome, rng)
        individual_id = f"g{generation}_{archetype_id}_{len(next_population):03d}"
        next_population.append(make_agent(individual_id, archetype_id, child_genome, initial_price))

    return next_population, weights
