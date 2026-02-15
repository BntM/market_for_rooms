"""Simulation runner: single runs and grid search."""

import copy
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import GridSearchConfig, SimulationConfig
from .environment import run_environment, run_environment_fast
from .metrics import StabilityMetrics, compute_metrics


def run_single_simulation(config: SimulationConfig) -> Tuple[StabilityMetrics, Dict[str, Any]]:
    """Run a single simulation and return metrics + daily detail."""
    state = run_environment_fast(config)
    metrics = compute_metrics(state, config.num_agents)

    daily_detail = {
        "utilization": {str(k): v for k, v in metrics.daily_utilization.items()},
        "avg_price": {str(k): v for k, v in metrics.daily_avg_price.items()},
    }

    return metrics, daily_detail


def run_grid_search(
    grid_config: GridSearchConfig,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Dict[str, Any]:
    """Run grid search over token_amounts x token_frequencies.

    Uses the fast-path runner (bypasses PettingZoo overhead) for each run.
    With ~0.13s per run, 280 runs complete in ~36s serially.

    Returns dict with:
      - best: {token_amount, token_frequency, stability_score, metrics}
      - all_results: list of {token_amount, token_frequency, avg_metrics}
      - heatmap: {amounts, frequencies, scores} for chart
    """
    all_results: List[Dict[str, Any]] = []
    total_combos = len(grid_config.token_amounts) * len(grid_config.token_frequencies)
    total_runs = total_combos * grid_config.num_seeds
    completed_runs = 0

    # Report 0 progress immediately so the UI sees the job is active
    if progress_callback:
        progress_callback(0.0)

    for amount in grid_config.token_amounts:
        for freq in grid_config.token_frequencies:
            seed_metrics: List[StabilityMetrics] = []

            for seed_offset in range(grid_config.num_seeds):
                cfg = copy.copy(grid_config.base_config)
                cfg.token_amount = amount
                cfg.token_frequency = freq
                cfg.seed = grid_config.base_seed + seed_offset

                state = run_environment_fast(cfg)
                metrics = compute_metrics(state, cfg.num_agents)
                seed_metrics.append(metrics)

                completed_runs += 1
                if progress_callback:
                    progress_callback(completed_runs / total_runs)

            # Average metrics across seeds
            avg = _average_metrics(seed_metrics)

            all_results.append({
                "token_amount": amount,
                "token_frequency": freq,
                "stability_score": avg.stability_score,
                "avg_satisfaction": avg.avg_satisfaction,
                "preference_match_rate": avg.preference_match_rate,
                "access_rate": avg.access_rate,
                "utilization_rate": avg.utilization_rate,
                "price_volatility": avg.price_volatility,
                "gini_coefficient": avg.gini_coefficient,
                "supply_demand_ratio": avg.supply_demand_ratio,
                "unmet_demand": avg.unmet_demand,
            })

    # Sort by stability score (lower = better)
    all_results.sort(key=lambda r: r["stability_score"])

    best = all_results[0] if all_results else None

    # Get daily detail for best config
    best_daily = {}
    if best:
        cfg = copy.copy(grid_config.base_config)
        cfg.token_amount = best["token_amount"]
        cfg.token_frequency = best["token_frequency"]
        cfg.seed = grid_config.base_seed
        _, best_daily = run_single_simulation(cfg)

    # Build heatmap data
    amounts = sorted(set(r["token_amount"] for r in all_results))
    frequencies = sorted(set(r["token_frequency"] for r in all_results))
    score_map = {(r["token_amount"], r["token_frequency"]): r["stability_score"] for r in all_results}
    heatmap_scores = []
    for freq in frequencies:
        row = []
        for amt in amounts:
            row.append(score_map.get((amt, freq), None))
        heatmap_scores.append(row)

    return {
        "best": best,
        "best_daily": best_daily,
        "all_results": all_results,
        "heatmap": {
            "amounts": amounts,
            "frequencies": frequencies,
            "scores": heatmap_scores,
        },
    }


def _average_metrics(metrics_list: List[StabilityMetrics]) -> StabilityMetrics:
    """Average a list of StabilityMetrics."""
    n = len(metrics_list)
    if n == 0:
        return StabilityMetrics()

    avg = StabilityMetrics()
    for m in metrics_list:
        avg.avg_satisfaction += m.avg_satisfaction
        avg.preference_match_rate += m.preference_match_rate
        avg.avg_consumer_surplus += m.avg_consumer_surplus
        avg.access_rate += m.access_rate
        avg.utilization_rate += m.utilization_rate
        avg.price_volatility += m.price_volatility
        avg.gini_coefficient += m.gini_coefficient
        avg.supply_demand_ratio += m.supply_demand_ratio
        avg.unmet_demand += m.unmet_demand
        avg.stability_score += m.stability_score

    avg.avg_satisfaction /= n
    avg.preference_match_rate /= n
    avg.avg_consumer_surplus /= n
    avg.access_rate /= n
    avg.utilization_rate /= n
    avg.price_volatility /= n
    avg.gini_coefficient /= n
    avg.supply_demand_ratio /= n
    avg.unmet_demand /= n
    avg.stability_score /= n

    return avg
