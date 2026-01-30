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
from .n_player_results import (
    NPlayerMatchupResult,
    save_n_player_results_csv,
    load_n_player_results_csv,
)
from .n_player_runner import NPlayerRunner, NPlayerGameConfig
from .n_player_analysis import (
    focal_wins,
    focal_losses,
    focal_win_rate_with_ci,
    baseline_win_rate,
    focal_mean_score,
    field_mean_score,
    focal_score_std_dev,
    focal_coefficient_of_variation,
    t_test_focal_vs_field,
    seat_win_rates,
)
# Alias to avoid name collision with analysis.summary_text
from .n_player_analysis import summary_text as n_player_summary_text

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
    # N-player modules
    "NPlayerMatchupResult",
    "save_n_player_results_csv",
    "load_n_player_results_csv",
    "NPlayerRunner",
    "NPlayerGameConfig",
    "focal_wins",
    "focal_losses",
    "focal_win_rate_with_ci",
    "baseline_win_rate",
    "focal_mean_score",
    "field_mean_score",
    "focal_score_std_dev",
    "focal_coefficient_of_variation",
    "t_test_focal_vs_field",
    "seat_win_rates",
    "n_player_summary_text",
]
