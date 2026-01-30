"""Focal-vs-field analysis functions for N-player simulation results.

All functions use stdlib math only (no numpy/scipy) for PyPy compatibility.
The focal agent's seat is stored in game.first_player (reusing the field).
"""

import math
from typing import Tuple

from src.simulation.n_player_results import NPlayerMatchupResult


def _focal_score(game) -> int:
    """Get the focal agent's score from a game."""
    return game.scores[game.first_player]


def _field_scores(game) -> Tuple[int, ...]:
    """Get all non-focal agent scores from a game."""
    return tuple(
        game.scores[i] for i in range(len(game.scores)) if i != game.first_player
    )


def _focal_won(game) -> bool | None:
    """Did the focal agent win? None if tie."""
    if game.winner is None:
        return None
    return game.winner == game.first_player


def focal_wins(result: NPlayerMatchupResult) -> int:
    """Count games won by the focal agent."""
    return sum(1 for g in result.games if _focal_won(g) is True)


def focal_losses(result: NPlayerMatchupResult) -> int:
    """Count games lost by the focal agent."""
    return sum(1 for g in result.games if _focal_won(g) is False)


def tie_count(result: NPlayerMatchupResult) -> int:
    """Count tied games."""
    return sum(1 for g in result.games if _focal_won(g) is None)


def focal_win_rate_with_ci(result: NPlayerMatchupResult) -> Tuple[float, float, float]:
    """Focal agent's win rate with 95% Wald confidence interval.

    Ties are excluded from the denominator.
    Returns (rate, ci_lo, ci_hi).
    """
    wins = focal_wins(result)
    losses = focal_losses(result)
    decisive = wins + losses

    if decisive == 0:
        return (0.0, 0.0, 0.0)

    rate = wins / decisive
    z = 1.96
    margin = z * math.sqrt(rate * (1 - rate) / decisive)
    return (rate, max(0.0, rate - margin), min(1.0, rate + margin))


def baseline_win_rate(result: NPlayerMatchupResult) -> float:
    """No-skill baseline win rate: 1/N."""
    return 1.0 / result.num_players


def focal_mean_score(result: NPlayerMatchupResult) -> float:
    """Mean score of the focal agent across all games."""
    n = len(result.games)
    if n == 0:
        return 0.0
    return sum(_focal_score(g) for g in result.games) / n


def field_mean_score(result: NPlayerMatchupResult) -> float:
    """Mean of all non-focal scores across all games."""
    n = len(result.games)
    if n == 0:
        return 0.0
    total = 0
    count = 0
    for g in result.games:
        for s in _field_scores(g):
            total += s
            count += 1
    if count == 0:
        return 0.0
    return total / count


def mean_score_advantage(result: NPlayerMatchupResult) -> float:
    """Focal mean score minus field mean score."""
    return focal_mean_score(result) - field_mean_score(result)


def focal_score_std_dev(result: NPlayerMatchupResult) -> float:
    """Standard deviation of focal agent's scores (Bessel's correction)."""
    n = len(result.games)
    if n < 2:
        return 0.0
    mean = focal_mean_score(result)
    var = sum((_focal_score(g) - mean) ** 2 for g in result.games) / (n - 1)
    return math.sqrt(var)


def focal_coefficient_of_variation(result: NPlayerMatchupResult) -> float:
    """Coefficient of variation (std / mean) for the focal agent."""
    mean = focal_mean_score(result)
    if mean == 0:
        return 0.0
    return focal_score_std_dev(result) / mean


def t_test_focal_vs_field(result: NPlayerMatchupResult) -> Tuple[float, float]:
    """One-sample t-test on per-game (focal - field_mean) differences.

    Tests whether the focal agent's score advantage is significantly
    different from zero. Returns (t_statistic, p_value).
    Uses normal approximation for p-value via math.erfc.
    """
    n = len(result.games)
    if n < 2:
        return (0.0, 1.0)

    diffs = []
    for g in result.games:
        f_scores = _field_scores(g)
        field_mean = sum(f_scores) / len(f_scores)
        diffs.append(_focal_score(g) - field_mean)

    d_mean = sum(diffs) / n
    d_var = sum((d - d_mean) ** 2 for d in diffs) / (n - 1)

    if d_var == 0:
        if d_mean == 0:
            return (0.0, 1.0)
        return (float("inf") if d_mean > 0 else float("-inf"), 0.0)

    d_std = math.sqrt(d_var)
    t_stat = d_mean / (d_std / math.sqrt(n))

    # Two-tailed p-value using normal approximation (accurate for large N)
    p_value = math.erfc(abs(t_stat) / math.sqrt(2))
    return (t_stat, p_value)


def seat_win_rates(result: NPlayerMatchupResult) -> Tuple[float, ...]:
    """Win rate for the focal agent by seat position.

    Returns a tuple of length num_players, where index i is the focal
    agent's win rate when seated in seat i.
    """
    n = result.num_players
    wins_by_seat = [0] * n
    games_by_seat = [0] * n

    for g in result.games:
        seat = g.first_player
        games_by_seat[seat] += 1
        if _focal_won(g) is True:
            wins_by_seat[seat] += 1

    rates = []
    for i in range(n):
        if games_by_seat[i] == 0:
            rates.append(0.0)
        else:
            rates.append(wins_by_seat[i] / games_by_seat[i])
    return tuple(rates)


def summary_text(result: NPlayerMatchupResult) -> str:
    """Human-readable summary of N-player matchup results."""
    n_games = len(result.games)
    f_wins = focal_wins(result)
    f_losses = focal_losses(result)
    ties = tie_count(result)
    rate, ci_lo, ci_hi = focal_win_rate_with_ci(result)
    baseline = baseline_win_rate(result)
    f_mean = focal_mean_score(result)
    fld_mean = field_mean_score(result)
    f_std = focal_score_std_dev(result)
    f_cv = focal_coefficient_of_variation(result)
    adv = mean_score_advantage(result)
    t_stat, p_val = t_test_focal_vs_field(result)
    s_rates = seat_win_rates(result)

    field_str = ", ".join(result.field_agent_names)
    seat_rates_str = ", ".join(
        f"seat {i}={r:.3f}" for i, r in enumerate(s_rates)
    )

    lines = [
        f"N-Player Matchup: {result.focal_agent_name} vs [{field_str}]",
        f"Players: {result.num_players}, Games: {n_games} "
        f"(seed {result.base_seed}, fast_mode={result.fast_mode})",
        f"Elapsed: {result.elapsed_seconds:.1f}s",
        "",
        f"Focal wins: {f_wins}, losses: {f_losses}, ties: {ties}",
        f"Focal win rate: {rate:.3f} [{ci_lo:.3f}, {ci_hi:.3f}]",
        f"Baseline (1/N): {baseline:.3f}",
        "",
        f"Focal mean score: {f_mean:.2f} (std={f_std:.2f}, CV={f_cv:.3f})",
        f"Field mean score: {fld_mean:.2f}",
        f"Mean score advantage: {adv:+.2f}",
        "",
        f"One-sample t-test (focal vs field): t={t_stat:.3f}, p={p_val:.4f}",
        f"Seat win rates: {seat_rates_str}",
    ]
    return "\n".join(lines)
