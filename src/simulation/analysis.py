"""Statistical analysis functions for simulation results.

All functions use stdlib math only (no numpy/scipy) for PyPy compatibility.
All account for seat alternation via game_index % 2.
"""

import math
from typing import Tuple

from src.simulation.results import MatchupResult


def _agent_a_score(game) -> int:
    """Get agent A's score from a game, accounting for seat alternation."""
    if game.first_player == 0:
        # Agent A is seat 0
        return game.scores[0]
    else:
        # Agent A is seat 1
        return game.scores[1]


def _agent_b_score(game) -> int:
    """Get agent B's score from a game, accounting for seat alternation."""
    if game.first_player == 0:
        # Agent B is seat 1
        return game.scores[1]
    else:
        # Agent B is seat 0
        return game.scores[0]


def _agent_a_won(game) -> bool | None:
    """Did agent A win? None if tie."""
    if game.winner is None:
        return None
    if game.first_player == 0:
        return game.winner == 0
    else:
        return game.winner == 1


def agent_a_wins(matchup: MatchupResult) -> int:
    """Count games won by agent A."""
    return sum(1 for g in matchup.games if _agent_a_won(g) is True)


def agent_b_wins(matchup: MatchupResult) -> int:
    """Count games won by agent B."""
    return sum(1 for g in matchup.games if _agent_a_won(g) is False)


def tie_count(matchup: MatchupResult) -> int:
    """Count tied games."""
    return sum(1 for g in matchup.games if _agent_a_won(g) is None)


def win_rate_with_ci(matchup: MatchupResult) -> Tuple[float, float, float]:
    """Agent A's win rate with 95% Wald confidence interval.

    Ties are excluded from the denominator.
    Returns (rate, ci_lo, ci_hi).
    """
    a_wins = agent_a_wins(matchup)
    b_wins = agent_b_wins(matchup)
    decisive = a_wins + b_wins

    if decisive == 0:
        return (0.0, 0.0, 0.0)

    rate = a_wins / decisive
    # 95% Wald interval: p +/- z * sqrt(p*(1-p)/n)
    z = 1.96
    margin = z * math.sqrt(rate * (1 - rate) / decisive)
    return (rate, max(0.0, rate - margin), min(1.0, rate + margin))


def mean_scores(matchup: MatchupResult) -> Tuple[float, float]:
    """Mean scores for agent A and agent B."""
    n = len(matchup.games)
    if n == 0:
        return (0.0, 0.0)
    a_total = sum(_agent_a_score(g) for g in matchup.games)
    b_total = sum(_agent_b_score(g) for g in matchup.games)
    return (a_total / n, b_total / n)


def score_std_dev(matchup: MatchupResult) -> Tuple[float, float]:
    """Standard deviation of scores for agent A and B (Bessel's correction)."""
    n = len(matchup.games)
    if n < 2:
        return (0.0, 0.0)

    a_mean, b_mean = mean_scores(matchup)
    a_var = sum((_agent_a_score(g) - a_mean) ** 2 for g in matchup.games) / (n - 1)
    b_var = sum((_agent_b_score(g) - b_mean) ** 2 for g in matchup.games) / (n - 1)
    return (math.sqrt(a_var), math.sqrt(b_var))


def coefficient_of_variation(matchup: MatchupResult) -> Tuple[float, float]:
    """Coefficient of variation (std / mean) for agent A and B."""
    a_mean, b_mean = mean_scores(matchup)
    a_std, b_std = score_std_dev(matchup)

    a_cv = a_std / a_mean if a_mean != 0 else 0.0
    b_cv = b_std / b_mean if b_mean != 0 else 0.0
    return (a_cv, b_cv)


def mean_score_advantage(matchup: MatchupResult) -> float:
    """Mean score of agent A minus mean score of agent B."""
    a_mean, b_mean = mean_scores(matchup)
    return a_mean - b_mean


def t_test_scores(matchup: MatchupResult) -> Tuple[float, float]:
    """Paired t-test on per-game score differences.

    Returns (t_statistic, p_value).
    Uses normal approximation for p-value via math.erfc.
    """
    n = len(matchup.games)
    if n < 2:
        return (0.0, 1.0)

    diffs = [_agent_a_score(g) - _agent_b_score(g) for g in matchup.games]
    d_mean = sum(diffs) / n
    d_var = sum((d - d_mean) ** 2 for d in diffs) / (n - 1)

    if d_var == 0:
        if d_mean == 0:
            return (0.0, 1.0)
        # All diffs identical and nonzero -- essentially infinite t
        return (float("inf") if d_mean > 0 else float("-inf"), 0.0)

    d_std = math.sqrt(d_var)
    t_stat = d_mean / (d_std / math.sqrt(n))

    # Two-tailed p-value using normal approximation (accurate for large N)
    p_value = math.erfc(abs(t_stat) / math.sqrt(2))
    return (t_stat, p_value)


def first_player_win_rate(matchup: MatchupResult) -> float:
    """Fraction of decisive games won by seat 0 (the first player)."""
    seat_0_wins = sum(1 for g in matchup.games if g.winner == 0)
    decisive = sum(1 for g in matchup.games if g.winner is not None)
    if decisive == 0:
        return 0.0
    return seat_0_wins / decisive


def summary_text(matchup: MatchupResult) -> str:
    """Human-readable summary of matchup results."""
    n = len(matchup.games)
    a_w = agent_a_wins(matchup)
    b_w = agent_b_wins(matchup)
    ties = tie_count(matchup)
    rate, ci_lo, ci_hi = win_rate_with_ci(matchup)
    a_mean, b_mean = mean_scores(matchup)
    a_std, b_std = score_std_dev(matchup)
    a_cv, b_cv = coefficient_of_variation(matchup)
    adv = mean_score_advantage(matchup)
    t_stat, p_val = t_test_scores(matchup)
    fp_rate = first_player_win_rate(matchup)

    lines = [
        f"Matchup: {matchup.agent_a_name} vs {matchup.agent_b_name}",
        f"Games: {n} (seed {matchup.base_seed}, fast_mode={matchup.fast_mode})",
        f"Elapsed: {matchup.elapsed_seconds:.1f}s",
        "",
        f"Wins: {matchup.agent_a_name}={a_w}, {matchup.agent_b_name}={b_w}, ties={ties}",
        f"Win rate ({matchup.agent_a_name}): {rate:.3f} [{ci_lo:.3f}, {ci_hi:.3f}]",
        "",
        f"Mean scores: {matchup.agent_a_name}={a_mean:.2f}, {matchup.agent_b_name}={b_mean:.2f}",
        f"Std dev: {matchup.agent_a_name}={a_std:.2f}, {matchup.agent_b_name}={b_std:.2f}",
        f"CV: {matchup.agent_a_name}={a_cv:.3f}, {matchup.agent_b_name}={b_cv:.3f}",
        f"Mean score advantage ({matchup.agent_a_name}): {adv:+.2f}",
        "",
        f"Paired t-test: t={t_stat:.3f}, p={p_val:.4f}",
        f"First-player win rate: {fp_rate:.3f}",
    ]
    return "\n".join(lines)
