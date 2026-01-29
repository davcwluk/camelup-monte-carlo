"""Simulation framework for batch game execution and analysis."""

from .results import GameResult, MatchupResult, save_results_csv, load_results_csv
from .runner import SimulationRunner, AGENT_REGISTRY, GameConfig
from .analysis import (
    agent_a_wins,
    agent_b_wins,
    tie_count,
    win_rate_with_ci,
    mean_scores,
    score_std_dev,
    coefficient_of_variation,
    mean_score_advantage,
    t_test_scores,
    first_player_win_rate,
    summary_text,
)

__all__ = [
    "GameResult",
    "MatchupResult",
    "save_results_csv",
    "load_results_csv",
    "SimulationRunner",
    "AGENT_REGISTRY",
    "GameConfig",
    "agent_a_wins",
    "agent_b_wins",
    "tie_count",
    "win_rate_with_ci",
    "mean_scores",
    "score_std_dev",
    "coefficient_of_variation",
    "mean_score_advantage",
    "t_test_scores",
    "first_player_win_rate",
    "summary_text",
]
