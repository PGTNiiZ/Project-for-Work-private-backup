from __future__ import annotations

import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.genetic_optimizer import GAConfig, GeneticOptimizer


class GeneticOptimizerTests(unittest.TestCase):
    def test_reproducible_and_improves_simple_fitness(self) -> None:
        config = GAConfig(population_size=12, generations=8, elite_size=2, seed=7)

        def fitness(genome):
            return sum(genome.feature_mask) / len(genome.feature_mask)

        first = GeneticOptimizer(8, config).optimize(fitness)
        second = GeneticOptimizer(8, config).optimize(fitness)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[1], second[1])
        self.assertGreaterEqual(first[1], first[2][0]["best_fitness"])

    def test_mutation_never_removes_every_feature(self) -> None:
        optimizer = GeneticOptimizer(5, GAConfig(population_size=4, generations=1, elite_size=1, mutation_rate=1.0))
        mutated = optimizer.mutate(optimizer.random_genome())
        self.assertTrue(any(mutated.feature_mask))

    def test_fitness_is_memoized(self) -> None:
        optimizer = GeneticOptimizer(3, GAConfig(population_size=4, generations=2, elite_size=1, crossover_rate=0.0, mutation_rate=0.0))
        calls = 0

        def fitness(genome):
            nonlocal calls
            calls += 1
            return float(sum(genome.feature_mask))

        optimizer.optimize(fitness)
        self.assertEqual(calls, len(optimizer.cache))


if __name__ == "__main__":
    unittest.main()
