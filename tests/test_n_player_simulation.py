"""Tests for N-player simulation framework."""

import math
import os
import tempfile

import pytest

from src.simulation.results import GameResult
from src.simulation.n_player_results import (
    NPlayerMatchupResult,
    save_n_player_results_csv,
    load_n_player_results_csv,
)
from src.simulation.n_player_runner import NPlayerRunner, NPlayerGameConfig
from src.simulation.n_player_analysis import (
    focal_wins,
    focal_losses,
    tie_count,
    focal_win_rate_with_ci,
    baseline_win_rate,
    focal_mean_score,
    field_mean_score,
    mean_score_advantage,
    focal_score_std_dev,
    focal_coefficient_of_variation,
    t_test_focal_vs_field,
    seat_win_rates,
    summary_text,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_n_game(game_index, scores, winner, focal_seat, seed=None,
                 num_legs=3, num_turns=20, agent_names=None):
    """Create a GameResult for N-player tests.

    Uses first_player to store focal_seat (matching N-player convention).
    """
    if seed is None:
        seed = 1000 + game_index
    if agent_names is None:
        n = len(scores)
        agent_names = tuple(f"Agent{i}" for i in range(n))
    return GameResult(
        game_index=game_index,
        seed=seed,
        scores=tuple(scores),
        winner=winner,
        num_legs=num_legs,
        num_turns=num_turns,
        agent_names=agent_names,
        first_player=focal_seat,
    )


def _make_n_matchup(games, focal_name="FocalAgent", field_names=("FieldA", "FieldB", "FieldC"),
                    num_players=4):
    return NPlayerMatchupResult(
        focal_agent_name=focal_name,
        field_agent_names=field_names,
        num_players=num_players,
        games=tuple(games),
        base_seed=1000,
        fast_mode=True,
        elapsed_seconds=1.0,
    )


def _four_player_fixture():
    """8 hand-crafted 4-player games. Focal wins 5, loses 2, tie 1.

    Focal agent rotates seats: game i -> seat (i % 4).
    """
    games = [
        # game 0: focal seat 0, focal wins
        _make_n_game(0, (20, 10, 5, 8), winner=0, focal_seat=0,
                     agent_names=("FocalAgent", "FieldA", "FieldB", "FieldC")),
        # game 1: focal seat 1, focal wins
        _make_n_game(1, (5, 18, 7, 3), winner=1, focal_seat=1,
                     agent_names=("FieldA", "FocalAgent", "FieldB", "FieldC")),
        # game 2: focal seat 2, focal loses (seat 0 wins)
        _make_n_game(2, (15, 6, 12, 4), winner=0, focal_seat=2,
                     agent_names=("FieldA", "FieldB", "FocalAgent", "FieldC")),
        # game 3: focal seat 3, focal wins
        _make_n_game(3, (3, 7, 9, 22), winner=3, focal_seat=3,
                     agent_names=("FieldA", "FieldB", "FieldC", "FocalAgent")),
        # game 4: focal seat 0, tie
        _make_n_game(4, (10, 10, 10, 10), winner=None, focal_seat=0,
                     agent_names=("FocalAgent", "FieldA", "FieldB", "FieldC")),
        # game 5: focal seat 1, focal wins
        _make_n_game(5, (4, 16, 8, 6), winner=1, focal_seat=1,
                     agent_names=("FieldA", "FocalAgent", "FieldB", "FieldC")),
        # game 6: focal seat 2, focal loses (seat 3 wins)
        _make_n_game(6, (7, 5, 11, 14), winner=3, focal_seat=2,
                     agent_names=("FieldA", "FieldB", "FocalAgent", "FieldC")),
        # game 7: focal seat 3, focal wins
        _make_n_game(7, (2, 4, 6, 19), winner=3, focal_seat=3,
                     agent_names=("FieldA", "FieldB", "FieldC", "FocalAgent")),
    ]
    return _make_n_matchup(games)


# ===========================================================================
# TestNPlayerMatchupResult
# ===========================================================================

class TestNPlayerMatchupResult:

    def test_frozen(self):
        m = _make_n_matchup([])
        with pytest.raises(AttributeError):
            m.focal_agent_name = "X"

    def test_fields(self):
        m = _make_n_matchup([], focal_name="Greedy",
                            field_names=("R1", "R2", "R3"), num_players=4)
        assert m.focal_agent_name == "Greedy"
        assert m.field_agent_names == ("R1", "R2", "R3")
        assert m.num_players == 4
        assert m.base_seed == 1000
        assert m.fast_mode is True

    def test_num_players_matches_field(self):
        m = _make_n_matchup([], field_names=("A", "B"), num_players=3)
        assert m.num_players == 1 + len(m.field_agent_names)


# ===========================================================================
# TestNPlayerCSVRoundTrip
# ===========================================================================

class TestNPlayerCSVRoundTrip:

    def test_save_and_load_4_player(self):
        result = _four_player_fixture()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_n_player_results_csv(result, path)
            loaded = load_n_player_results_csv(path)

            assert loaded.num_players == 4
            assert loaded.focal_agent_name == "FocalAgent"
            assert len(loaded.field_agent_names) == 3
            assert len(loaded.games) == 8

            for orig, ldg in zip(result.games, loaded.games):
                assert orig.game_index == ldg.game_index
                assert orig.seed == ldg.seed
                assert orig.scores == ldg.scores
                assert orig.winner == ldg.winner
                assert orig.num_legs == ldg.num_legs
                assert orig.num_turns == ldg.num_turns
                assert orig.agent_names == ldg.agent_names
                assert orig.first_player == ldg.first_player
        finally:
            os.unlink(path)

    def test_csv_handles_ties(self):
        games = [
            _make_n_game(0, (8, 8, 8, 8), winner=None, focal_seat=0,
                         agent_names=("FocalAgent", "FieldA", "FieldB", "FieldC")),
        ]
        result = _make_n_matchup(games)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_n_player_results_csv(result, path)
            loaded = load_n_player_results_csv(path)
            assert loaded.games[0].winner is None
        finally:
            os.unlink(path)

    def test_dynamic_columns(self):
        """CSV has score_0..score_3 and agent_seat_0..agent_seat_3 for 4 players."""
        games = [
            _make_n_game(0, (10, 5, 3, 7), winner=0, focal_seat=0,
                         agent_names=("FocalAgent", "FieldA", "FieldB", "FieldC")),
        ]
        result = _make_n_matchup(games)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_n_player_results_csv(result, path)
            with open(path) as f:
                header = f.readline().strip()
            assert "score_0" in header
            assert "score_3" in header
            assert "agent_seat_0" in header
            assert "agent_seat_3" in header
            assert "focal_seat" in header
            # Should not have score_4 (only 4 players)
            assert "score_4" not in header
        finally:
            os.unlink(path)


# ===========================================================================
# TestNPlayerRunner
# ===========================================================================

class TestNPlayerRunner:

    def test_validates_focal_agent_name(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            NPlayerRunner("BogusAgent", ("RandomAgent", "RandomAgent"), num_games=1)

    def test_validates_field_agent_names(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            NPlayerRunner("RandomAgent", ("BogusAgent", "RandomAgent"), num_games=1)

    def test_serial_4_player(self):
        runner = NPlayerRunner(
            "RandomAgent", ("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=8, base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        assert isinstance(result, NPlayerMatchupResult)
        assert len(result.games) == 8
        assert result.num_players == 4
        assert result.focal_agent_name == "RandomAgent"
        # Each game should have 4 scores
        for game in result.games:
            assert len(game.scores) == 4

    def test_parallel_4_player(self):
        runner = NPlayerRunner(
            "RandomAgent", ("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=8, base_seed=42, fast_mode=True, num_workers=2,
        )
        result = runner.run()
        assert len(result.games) == 8
        assert result.num_players == 4

    def test_deterministic(self):
        kwargs = dict(
            focal_agent_name="RandomAgent",
            field_agent_names=("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=8, base_seed=42, fast_mode=True, num_workers=1,
        )
        r1 = NPlayerRunner(**kwargs).run()
        r2 = NPlayerRunner(**kwargs).run()
        for g1, g2 in zip(r1.games, r2.games):
            assert g1.scores == g2.scores
            assert g1.winner == g2.winner

    def test_seat_rotation(self):
        """Focal agent cycles through all seats."""
        runner = NPlayerRunner(
            "RandomAgent", ("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=8, base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        for game in result.games:
            expected_seat = game.game_index % 4
            assert game.first_player == expected_seat

    def test_2_player_equivalent(self):
        """N-player runner with 2 players produces valid results."""
        runner = NPlayerRunner(
            "RandomAgent", ("RandomAgent",),
            num_games=6, base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        assert result.num_players == 2
        assert len(result.games) == 6
        for game in result.games:
            assert len(game.scores) == 2

    def test_seeds_are_sequential(self):
        runner = NPlayerRunner(
            "RandomAgent", ("RandomAgent", "RandomAgent"),
            num_games=5, base_seed=100, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        for game in result.games:
            assert game.seed == 100 + game.game_index


# ===========================================================================
# TestNPlayerAnalysis
# ===========================================================================

class TestNPlayerAnalysis:

    def test_focal_wins_count(self):
        m = _four_player_fixture()
        assert focal_wins(m) == 5

    def test_focal_losses_count(self):
        m = _four_player_fixture()
        assert focal_losses(m) == 2

    def test_tie_count(self):
        m = _four_player_fixture()
        assert tie_count(m) == 1

    def test_focal_win_rate_basic(self):
        m = _four_player_fixture()
        rate, ci_lo, ci_hi = focal_win_rate_with_ci(m)
        # 5 wins out of 7 decisive -> 5/7 ~ 0.714
        assert abs(rate - 5 / 7) < 0.001
        assert ci_lo < rate
        assert ci_hi > rate

    def test_baseline_win_rate(self):
        m = _four_player_fixture()
        assert abs(baseline_win_rate(m) - 0.25) < 0.001

    def test_focal_mean_score(self):
        m = _four_player_fixture()
        # Focal scores by seat: game 0=20, 1=18, 2=12, 3=22, 4=10, 5=16, 6=11, 7=19
        expected = (20 + 18 + 12 + 22 + 10 + 16 + 11 + 19) / 8
        assert abs(focal_mean_score(m) - expected) < 0.001

    def test_field_mean_score(self):
        m = _four_player_fixture()
        # Field scores per game (all non-focal):
        # game 0: 10,5,8  game 1: 5,7,3  game 2: 15,6,4  game 3: 3,7,9
        # game 4: 10,10,10  game 5: 4,8,6  game 6: 7,5,14  game 7: 2,4,6
        field_total = (10+5+8) + (5+7+3) + (15+6+4) + (3+7+9) + \
                      (10+10+10) + (4+8+6) + (7+5+14) + (2+4+6)
        expected = field_total / (8 * 3)  # 8 games, 3 field agents each
        assert abs(field_mean_score(m) - expected) < 0.001

    def test_mean_score_advantage(self):
        m = _four_player_fixture()
        adv = mean_score_advantage(m)
        f_mean = focal_mean_score(m)
        fld_mean = field_mean_score(m)
        assert abs(adv - (f_mean - fld_mean)) < 0.001
        # Focal should be ahead
        assert adv > 0

    def test_focal_score_std_dev(self):
        m = _four_player_fixture()
        scores = [20, 18, 12, 22, 10, 16, 11, 19]
        mean = sum(scores) / len(scores)
        var = sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)
        expected_std = math.sqrt(var)
        assert abs(focal_score_std_dev(m) - expected_std) < 0.001

    def test_focal_cv(self):
        m = _four_player_fixture()
        std = focal_score_std_dev(m)
        mean = focal_mean_score(m)
        assert abs(focal_coefficient_of_variation(m) - std / mean) < 0.001

    def test_t_test_significant(self):
        """Focal clearly better than field -> significant t-test."""
        # 20 games where focal always scores 20, field averages ~5
        games = []
        for i in range(20):
            focal_seat = i % 4
            scores = [5, 5, 5, 5]
            scores[focal_seat] = 20
            names = ["FieldA", "FieldB", "FieldC", "FieldD"]
            names[focal_seat] = "FocalAgent"
            games.append(_make_n_game(i, scores, winner=focal_seat,
                                      focal_seat=focal_seat,
                                      agent_names=tuple(names)))
        m = _make_n_matchup(games, field_names=("FieldA", "FieldB", "FieldC"))
        t_stat, p_val = t_test_focal_vs_field(m)
        assert p_val < 0.001

    def test_t_test_not_significant(self):
        """All equal scores -> not significant."""
        games = []
        for i in range(20):
            focal_seat = i % 4
            names = ["FieldA", "FieldB", "FieldC", "FieldD"]
            names[focal_seat] = "FocalAgent"
            games.append(_make_n_game(i, (10, 10, 10, 10), winner=None,
                                      focal_seat=focal_seat,
                                      agent_names=tuple(names)))
        m = _make_n_matchup(games, field_names=("FieldA", "FieldB", "FieldC"))
        t_stat, p_val = t_test_focal_vs_field(m)
        assert abs(t_stat) < 0.001
        assert p_val > 0.95

    def test_seat_win_rates(self):
        m = _four_player_fixture()
        rates = seat_win_rates(m)
        assert len(rates) == 4
        # Seat 0: games 0,4 -> focal wins game 0, ties game 4 -> 1 win / 2 games
        assert abs(rates[0] - 0.5) < 0.001
        # Seat 1: games 1,5 -> focal wins both -> 2/2
        assert abs(rates[1] - 1.0) < 0.001
        # Seat 2: games 2,6 -> focal loses both -> 0/2
        assert abs(rates[2] - 0.0) < 0.001
        # Seat 3: games 3,7 -> focal wins both -> 2/2
        assert abs(rates[3] - 1.0) < 0.001

    def test_summary_text(self):
        m = _four_player_fixture()
        text = summary_text(m)
        assert "N-Player Matchup" in text
        assert "FocalAgent" in text
        assert "Baseline (1/N)" in text
        assert "Seat win rates" in text


# ===========================================================================
# TestNPlayerEndToEnd
# ===========================================================================

class TestNPlayerEndToEnd:

    def test_full_pipeline(self):
        """Runner -> CSV -> load -> analysis -> summary_text."""
        runner = NPlayerRunner(
            "RandomAgent",
            ("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=12, base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_n_player_results_csv(result, path)
            loaded = load_n_player_results_csv(path)

            assert len(loaded.games) == 12
            assert loaded.num_players == 4
            for orig, ldg in zip(result.games, loaded.games):
                assert orig.scores == ldg.scores
                assert orig.winner == ldg.winner

            text = summary_text(loaded)
            assert "RandomAgent" in text
            assert "N-Player Matchup" in text
        finally:
            os.unlink(path)

    def test_greedy_vs_3_random_wins(self):
        """GreedyAgent vs 3 RandomAgents should win >> 25% (1/N baseline)."""
        runner = NPlayerRunner(
            "GreedyAgent",
            ("RandomAgent", "RandomAgent", "RandomAgent"),
            num_games=20, base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()

        rate, ci_lo, ci_hi = focal_win_rate_with_ci(result)
        # Greedy should dominate random opponents
        assert rate > 0.25, f"Greedy win rate {rate:.3f} should exceed 1/N baseline 0.25"
        adv = mean_score_advantage(result)
        assert adv > 0, f"Greedy score advantage {adv:.2f} should be positive"
