"""Frozen B0-B3 decision policies for authoritative v2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.stats import qmc

NO_MATCH, REVIEW, MATCH = 0, 1, 2
B0_FIXED = (0.98, 0.95)
BOUNDS = np.array([[0.90, 0.999], [0.50, 0.90], [0.50, 1.0], [0.0, 0.60]])


def b0_decide(prob: np.ndarray, thresholds: tuple[float, float] = B0_FIXED) -> np.ndarray:
    """Fixed simple policy: MATCH, REVIEW, then NO_MATCH."""
    t_match, t_review = thresholds
    result = np.full(prob.shape, NO_MATCH, dtype=np.int8)
    result[prob >= t_review] = REVIEW
    result[prob >= t_match] = MATCH
    return result


def decide_four_parameter(prob: np.ndarray, name_sim: np.ndarray, genome: tuple[float, ...]) -> np.ndarray:
    """Shared B2/B3 semantics for [t_match,t_review,c_promote,c_demote]."""
    t_match, t_review, c_promote, c_demote = genome
    if not (0.90 <= t_match <= 0.999 and 0.50 <= t_review <= t_match):
        raise ValueError("invalid probability thresholds")
    if not (0.50 <= c_promote <= 1.0 and 0.0 <= c_demote <= c_promote):
        raise ValueError("invalid name thresholds")
    result = np.full(prob.shape, REVIEW, dtype=np.int8)
    result[prob < t_review] = NO_MATCH
    band = (prob >= t_review) & (prob < t_match)
    result[band & (name_sim >= c_promote)] = MATCH
    result[band & (name_sim < c_demote)] = NO_MATCH
    result[prob >= t_match] = MATCH
    return result


def _cost(decisions: np.ndarray, actual: np.ndarray) -> float:
    return float(
        2.0 * np.sum((decisions == MATCH) & (actual == 0))
        + np.sum((decisions == NO_MATCH) & (actual == 1))
        + 0.1 * np.sum(decisions == REVIEW)
    )


def _simple_genome(point: np.ndarray) -> tuple[float, float]:
    t_match, t_review = point
    return float(max(t_match, t_review)), float(min(t_match, t_review))


def b1_search(prob: np.ndarray, actual: np.ndarray, *, budget: int, seed: int = 0) -> tuple[tuple[float, float], dict[str, int]]:
    """Deterministic Sobol search over B0's two-threshold family."""
    sampler = qmc.Sobol(d=2, scramble=False)
    points = qmc.scale(sampler.random(n=budget), [0.90, 0.50], [0.999, 0.999])
    best, best_cost = None, float("inf")
    evaluations = 0
    for point in points:
        genome = _simple_genome(point)
        decisions = b0_decide(prob, genome)
        value = _cost(decisions, actual)
        evaluations += 1
        if value < best_cost:
            best, best_cost = genome, value
    return best, {"requested_evaluations": budget, "realized_evaluations": evaluations}


def _valid_genome(point: np.ndarray) -> tuple[float, float, float, float]:
    t_match, t_review, cp, cd = point
    return (float(t_match), float(min(t_review, t_match)), float(cp), float(min(cd, cp)))


def b2_sobol_search(prob: np.ndarray, name_sim: np.ndarray, actual: np.ndarray, *, budget: int, seed: int = 0):
    """Deterministic Sobol optimizer for the exact B3 policy class."""
    sampler = qmc.Sobol(d=4, scramble=False)
    points = qmc.scale(sampler.random(n=budget), BOUNDS[:, 0], BOUNDS[:, 1])
    return _search_points(points, lambda g: _cost(decide_four_parameter(prob, name_sim, g), actual), budget)


def _search_points(points: np.ndarray, objective: Callable[[tuple[float, ...]], float], budget: int):
    best, best_cost = None, float("inf")
    evaluations = 0
    for point in points:
        genome = _valid_genome(point)
        value = objective(genome)
        evaluations += 1
        if value < best_cost:
            best, best_cost = genome, value
    return best, {"requested_evaluations": budget, "realized_evaluations": evaluations}


def b3_ga_search(prob: np.ndarray, name_sim: np.ndarray, actual: np.ndarray, *, budget: int, seed: int = 0):
    """Seeded GA over the same four-dimensional class and exact evaluation budget."""
    rng = np.random.default_rng(seed)
    population_size = 60
    population = rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1], size=(population_size, 4))
    evaluations = 0
    best, best_cost = None, float("inf")
    while evaluations < budget:
        scores = []
        for point in population:
            if evaluations >= budget:
                break
            genome = _valid_genome(point)
            value = _cost(decide_four_parameter(prob, name_sim, genome), actual)
            evaluations += 1
            scores.append((value, genome))
            if value < best_cost:
                best, best_cost = genome, value
        if evaluations >= budget:
            break
        scores.sort(key=lambda item: item[0])
        elite = np.array([item[1] for item in scores[: max(2, len(scores) // 5)]])
        population = np.vstack([elite, elite[rng.integers(len(elite), size=population_size-len(elite))]])
        population += rng.normal(0, 0.02, population.shape) * (rng.random(population.shape) < 0.30)
        population = np.clip(population, BOUNDS[:, 0], BOUNDS[:, 1])
    return best, {"requested_evaluations": budget, "realized_evaluations": evaluations}
