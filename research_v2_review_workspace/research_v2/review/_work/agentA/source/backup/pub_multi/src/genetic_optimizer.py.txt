"""Small, dependency-free genetic optimizer used by the model tuning pipeline.

The optimizer maximizes a user supplied fitness function.  Keeping the search
engine independent from scikit-learn makes it easy to test and reuse for other
pipeline stages (for example, blocking-rule or CRM-threshold optimization).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
import random
from typing import Callable, Sequence


@dataclass(frozen=True)
class Genome:
    """Feature selection and GradientBoosting hyperparameters."""

    feature_mask: tuple[bool, ...]
    n_estimators: int
    learning_rate: float
    max_depth: int
    min_samples_leaf: int
    subsample: float
    threshold: float

    def cache_key(self) -> tuple[object, ...]:
        """Stable, rounded identity suitable for memoizing expensive fits."""
        return (
            self.feature_mask,
            self.n_estimators,
            round(self.learning_rate, 6),
            self.max_depth,
            self.min_samples_leaf,
            round(self.subsample, 6),
            round(self.threshold, 6),
        )


@dataclass(frozen=True)
class Bounds:
    n_estimators: tuple[int, int] = (100, 500)
    learning_rate: tuple[float, float] = (0.01, 0.15)
    max_depth: tuple[int, int] = (2, 8)
    min_samples_leaf: tuple[int, int] = (1, 12)
    subsample: tuple[float, float] = (0.60, 1.0)
    threshold: tuple[float, float] = (0.20, 0.95)


@dataclass(frozen=True)
class GAConfig:
    population_size: int = 20
    generations: int = 12
    elite_size: int = 2
    tournament_size: int = 3
    crossover_rate: float = 0.80
    mutation_rate: float = 0.15
    seed: int = 42

    def validate(self) -> None:
        if self.population_size < 2:
            raise ValueError("population_size must be at least 2")
        if self.generations < 1:
            raise ValueError("generations must be at least 1")
        if not 1 <= self.elite_size < self.population_size:
            raise ValueError("elite_size must be in [1, population_size)")
        if not 1 <= self.tournament_size <= self.population_size:
            raise ValueError("tournament_size must be in [1, population_size]")
        for name, value in (("crossover_rate", self.crossover_rate), ("mutation_rate", self.mutation_rate)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


class GeneticOptimizer:
    """A deterministic elitist GA with tournament selection and memoization."""

    def __init__(self, feature_count: int, config: GAConfig, bounds: Bounds | None = None):
        if feature_count < 1:
            raise ValueError("feature_count must be at least 1")
        config.validate()
        self.feature_count = feature_count
        self.config = config
        self.bounds = bounds or Bounds()
        self.rng = random.Random(config.seed)
        self.cache: dict[tuple[object, ...], float] = {}

    def random_genome(self) -> Genome:
        mask = tuple(self.rng.random() < 0.70 for _ in range(self.feature_count))
        mask = self._ensure_feature(mask)
        return Genome(
            feature_mask=mask,
            n_estimators=self.rng.randint(*self.bounds.n_estimators),
            learning_rate=self._log_uniform(*self.bounds.learning_rate),
            max_depth=self.rng.randint(*self.bounds.max_depth),
            min_samples_leaf=self.rng.randint(*self.bounds.min_samples_leaf),
            subsample=self.rng.uniform(*self.bounds.subsample),
            threshold=self.rng.uniform(*self.bounds.threshold),
        )

    def optimize(
        self,
        evaluate: Callable[[Genome], float],
        on_generation: Callable[[int, Sequence[tuple[Genome, float]]], None] | None = None,
    ) -> tuple[Genome, float, list[dict[str, float]]]:
        population = [self.random_genome() for _ in range(self.config.population_size)]
        history: list[dict[str, float]] = []

        for generation in range(1, self.config.generations + 1):
            ranked = self._rank(population, evaluate)
            scores = [score for _, score in ranked]
            history.append(
                {
                    "generation": generation,
                    "best_fitness": scores[0],
                    "mean_fitness": sum(scores) / len(scores),
                    "unique_evaluations": len(self.cache),
                }
            )
            if on_generation:
                on_generation(generation, ranked)

            if generation == self.config.generations:
                population = [genome for genome, _ in ranked]
                break

            elites = [genome for genome, _ in ranked[: self.config.elite_size]]
            next_population = list(elites)
            while len(next_population) < self.config.population_size:
                parent_a = self._tournament(ranked)
                parent_b = self._tournament(ranked)
                child = self.crossover(parent_a, parent_b)
                next_population.append(self.mutate(child))
            population = next_population

        best, score = self._rank(population, evaluate)[0]
        return best, score, history

    def crossover(self, left: Genome, right: Genome) -> Genome:
        if self.rng.random() >= self.config.crossover_rate:
            return left
        mask = tuple(a if self.rng.random() < 0.5 else b for a, b in zip(left.feature_mask, right.feature_mask))
        return Genome(
            feature_mask=self._ensure_feature(mask),
            n_estimators=self._pick(left.n_estimators, right.n_estimators),
            learning_rate=self._pick(left.learning_rate, right.learning_rate),
            max_depth=self._pick(left.max_depth, right.max_depth),
            min_samples_leaf=self._pick(left.min_samples_leaf, right.min_samples_leaf),
            subsample=self._pick(left.subsample, right.subsample),
            threshold=self._pick(left.threshold, right.threshold),
        )

    def mutate(self, genome: Genome) -> Genome:
        rate = self.config.mutation_rate
        mask = tuple((not bit) if self.rng.random() < rate else bit for bit in genome.feature_mask)
        mutated = replace(genome, feature_mask=self._ensure_feature(mask))
        if self.rng.random() < rate:
            mutated = replace(mutated, n_estimators=self._jitter_int(mutated.n_estimators, 50, self.bounds.n_estimators))
        if self.rng.random() < rate:
            value = mutated.learning_rate * math.exp(self.rng.gauss(0.0, 0.30))
            mutated = replace(mutated, learning_rate=self._clip(value, self.bounds.learning_rate))
        if self.rng.random() < rate:
            mutated = replace(mutated, max_depth=self._jitter_int(mutated.max_depth, 1, self.bounds.max_depth))
        if self.rng.random() < rate:
            mutated = replace(mutated, min_samples_leaf=self._jitter_int(mutated.min_samples_leaf, 2, self.bounds.min_samples_leaf))
        if self.rng.random() < rate:
            mutated = replace(mutated, subsample=self._clip(mutated.subsample + self.rng.gauss(0.0, 0.08), self.bounds.subsample))
        if self.rng.random() < rate:
            mutated = replace(mutated, threshold=self._clip(mutated.threshold + self.rng.gauss(0.0, 0.08), self.bounds.threshold))
        return mutated

    def _rank(self, population: Sequence[Genome], evaluate: Callable[[Genome], float]) -> list[tuple[Genome, float]]:
        scored = []
        for genome in population:
            key = genome.cache_key()
            if key not in self.cache:
                score = float(evaluate(genome))
                if not math.isfinite(score):
                    raise ValueError("fitness function returned a non-finite value")
                self.cache[key] = score
            scored.append((genome, self.cache[key]))
        return sorted(scored, key=lambda item: item[1], reverse=True)

    def _tournament(self, ranked: Sequence[tuple[Genome, float]]) -> Genome:
        contenders = self.rng.sample(list(ranked), self.config.tournament_size)
        return max(contenders, key=lambda item: item[1])[0]

    def _ensure_feature(self, mask: tuple[bool, ...]) -> tuple[bool, ...]:
        if any(mask):
            return mask
        values = list(mask)
        values[self.rng.randrange(self.feature_count)] = True
        return tuple(values)

    def _pick(self, left: object, right: object):
        return left if self.rng.random() < 0.5 else right

    def _jitter_int(self, value: int, radius: int, bounds: tuple[int, int]) -> int:
        return int(min(bounds[1], max(bounds[0], value + self.rng.randint(-radius, radius))))

    def _log_uniform(self, lower: float, upper: float) -> float:
        return math.exp(self.rng.uniform(math.log(lower), math.log(upper)))

    @staticmethod
    def _clip(value: float, bounds: tuple[float, float]) -> float:
        return min(bounds[1], max(bounds[0], value))
