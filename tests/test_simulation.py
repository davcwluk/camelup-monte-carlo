"""Tests for Phase 4 simulation framework."""

import math
import os
import tempfile

import pytest

from src.simulation.results import (
    GameResult, MatchupResult, save_results_csv, load_results_csv,
)
from src.simulation.runner import SimulationRunner, AGENT_REGISTRY
from src.simulation.analysis import (
    agent_a_wins, agent_b_wins, tie_count,
    win_rate_with_ci, mean_scores, score_std_dev,
    coefficient_of_variation, mean_score_advantage,
    t_test_scores, first_player_win_rate, summary_text,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_game(game_index, scores, winner, first_player=None, seed=None,
               num_legs=3, num_turns=20, agent_names=None):
    """Create a GameResult with sensible defaults."""
    if first_player is None:
        first_player = 0 if game_index % 2 == 0 else 1
    if seed is None:
        seed = 1000 + game_index
    if agent_names is None:
        if first_player == 0:
            agent_names = ("AgentA", "AgentB")
        else:
            agent_names = ("AgentB", "AgentA")
    return GameResult(
        game_index=game_index,
        seed=seed,
        scores=tuple(scores),
        winner=winner,
        num_legs=num_legs,
        num_turns=num_turns,
        agent_names=agent_names,
        first_player=first_player,
    )


def _make_matchup(games, agent_a="AgentA", agent_b="AgentB"):
    return MatchupResult(
        agent_a_name=agent_a,
        agent_b_name=agent_b,
        games=tuple(games),
        base_seed=1000,
        fast_mode=True,
        elapsed_seconds=1.0,
    )


# ===========================================================================
# TestGameResult
# ===========================================================================

class TestGameResult:

    def test_game_result_frozen(self):
        g = _make_game(0, (10, 5), winner=0)
        with pytest.raises(AttributeError):
            g.game_index = 99

    def test_game_result_fields(self):
        g = _make_game(3, (7, 12), winner=1, seed=42, num_legs=4, num_turns=30)
        assert g.game_index == 3
        assert g.seed == 42
        assert g.scores == (7, 12)
        assert g.winner == 1
        assert g.num_legs == 4
        assert g.num_turns == 30

    def test_game_result_tie(self):
        g = _make_game(0, (8, 8), winner=None)
        assert g.winner is None

    def test_game_result_scores_tuple(self):
        g = _make_game(0, (5, 10), winner=1)
        assert isinstance(g.scores, tuple)
        assert all(isinstance(s, int) for s in g.scores)


# ===========================================================================
# TestMatchupResult
# ===========================================================================

class TestMatchupResult:

    def test_matchup_result_frozen(self):
        m = _make_matchup([])
        with pytest.raises(AttributeError):
            m.agent_a_name = "X"

    def test_matchup_result_games_tuple(self):
        games = [_make_game(0, (10, 5), winner=0)]
        m = _make_matchup(games)
        assert isinstance(m.games, tuple)

    def test_matchup_result_metadata(self):
        m = _make_matchup([], agent_a="Greedy", agent_b="Random")
        assert m.agent_a_name == "Greedy"
        assert m.agent_b_name == "Random"
        assert m.base_seed == 1000
        assert m.fast_mode is True


# ===========================================================================
# TestCSVRoundTrip
# ===========================================================================

class TestCSVRoundTrip:

    def test_save_and_load_csv(self):
        games = [
            # Even index: A is seat 0, first_player=0
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            # Odd index: B is seat 0, first_player=1
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            _make_game(2, (7, 7), winner=None, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(3, (4, 9), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            _make_game(4, (15, 2), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
        ]
        matchup = _make_matchup(games)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_results_csv(matchup, path)
            loaded = load_results_csv(path)

            assert len(loaded.games) == 5
            for orig, loaded_g in zip(matchup.games, loaded.games):
                assert orig.game_index == loaded_g.game_index
                assert orig.seed == loaded_g.seed
                assert orig.scores == loaded_g.scores
                assert orig.winner == loaded_g.winner
                assert orig.num_legs == loaded_g.num_legs
                assert orig.num_turns == loaded_g.num_turns
                assert orig.agent_names == loaded_g.agent_names
                assert orig.first_player == loaded_g.first_player
        finally:
            os.unlink(path)

    def test_csv_handles_ties(self):
        games = [
            _make_game(0, (8, 8), winner=None, first_player=0,
                       agent_names=("AgentA", "AgentB")),
        ]
        matchup = _make_matchup(games)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_results_csv(matchup, path)
            loaded = load_results_csv(path)
            assert loaded.games[0].winner is None
        finally:
            os.unlink(path)

    def test_csv_column_headers(self):
        games = [_make_game(0, (10, 5), winner=0, first_player=0,
                            agent_names=("AgentA", "AgentB"))]
        matchup = _make_matchup(games)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name

        try:
            save_results_csv(matchup, path)
            with open(path) as f:
                header = f.readline().strip()
            expected = "game_index,seed,score_0,score_1,winner,num_legs,num_turns,agent_seat_0,agent_seat_1,first_player"
            assert header == expected
        finally:
            os.unlink(path)


# ===========================================================================
# TestSimulationRunner
# ===========================================================================

class TestSimulationRunner:

    def test_runner_validates_agent_names(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            SimulationRunner("BogusAgent", "RandomAgent", num_games=1)
        with pytest.raises(ValueError, match="Unknown agent"):
            SimulationRunner("RandomAgent", "NoSuchAgent", num_games=1)

    def test_runner_serial_random_vs_random(self):
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=10,
            base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        assert isinstance(result, MatchupResult)
        assert len(result.games) == 10
        assert result.agent_a_name == "RandomAgent"
        assert result.agent_b_name == "RandomAgent"

    def test_runner_serial_deterministic(self):
        kwargs = dict(
            agent_a_name="RandomAgent", agent_b_name="RandomAgent",
            num_games=10, base_seed=42, fast_mode=True, num_workers=1,
        )
        r1 = SimulationRunner(**kwargs).run()
        r2 = SimulationRunner(**kwargs).run()
        for g1, g2 in zip(r1.games, r2.games):
            assert g1.scores == g2.scores
            assert g1.winner == g2.winner

    def test_runner_parallel_random_vs_random(self):
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=20,
            base_seed=42, fast_mode=True, num_workers=2,
        )
        result = runner.run()
        assert len(result.games) == 20

    def test_runner_parallel_deterministic(self):
        kwargs = dict(
            agent_a_name="RandomAgent", agent_b_name="RandomAgent",
            num_games=20, base_seed=42, fast_mode=True,
        )
        serial = SimulationRunner(num_workers=1, **kwargs).run()
        parallel = SimulationRunner(num_workers=2, **kwargs).run()
        for s, p in zip(serial.games, parallel.games):
            assert s.scores == p.scores
            assert s.winner == p.winner

    def test_runner_alternates_start_player(self):
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=10,
            base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        for game in result.games:
            expected = 0 if game.game_index % 2 == 0 else 1
            assert game.first_player == expected

    def test_runner_greedy_vs_random(self):
        runner = SimulationRunner(
            "GreedyAgent", "RandomAgent", num_games=4,
            base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        assert len(result.games) == 4
        for game in result.games:
            assert game.num_turns > 0
            assert game.num_legs >= 1

    def test_runner_seeds_are_sequential(self):
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=5,
            base_seed=100, fast_mode=True, num_workers=1,
        )
        result = runner.run()
        for game in result.games:
            assert game.seed == 100 + game.game_index

    def test_runner_all_agent_types(self):
        for agent_name in AGENT_REGISTRY:
            runner = SimulationRunner(
                agent_name, "RandomAgent", num_games=2,
                base_seed=42, fast_mode=True, num_workers=1,
            )
            result = runner.run()
            assert len(result.games) == 2

    def test_runner_progress_output(self, capsys):
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=10,
            base_seed=42, fast_mode=True, num_workers=1,
            progress_interval=5,
        )
        runner.run()
        captured = capsys.readouterr()
        assert "5/10" in captured.out
        assert "10/10" in captured.out


# ===========================================================================
# TestAnalysis
# ===========================================================================

class TestAnalysis:

    def _six_game_matchup(self):
        """6 hand-crafted games: A wins 4, B wins 1, tie 1."""
        games = [
            # game 0: even -> A seat 0, A wins (winner=0)
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            # game 1: odd -> B seat 0, A wins (winner=1, A is seat 1)
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            # game 2: even -> A seat 0, A wins (winner=0)
            _make_game(2, (9, 4), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            # game 3: odd -> B seat 0, B wins (winner=0, B is seat 0)
            _make_game(3, (11, 6), winner=0, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            # game 4: even -> A seat 0, tie
            _make_game(4, (8, 8), winner=None, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            # game 5: odd -> B seat 0, A wins (winner=1)
            _make_game(5, (2, 14), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        return _make_matchup(games)

    def test_agent_wins_counting(self):
        m = self._six_game_matchup()
        assert agent_a_wins(m) == 4
        assert agent_b_wins(m) == 1
        assert tie_count(m) == 1

    def test_agent_wins_with_alternation(self):
        """Verify correct counting despite seat swaps."""
        m = self._six_game_matchup()
        # Agent A wins games 0, 1, 2, 5. Agent B wins game 3. Game 4 tie.
        assert agent_a_wins(m) == 4
        assert agent_b_wins(m) == 1

    def test_win_rate_with_ci_basic(self):
        # 60 wins out of 100 decisive games
        games = []
        for i in range(100):
            fp = 0 if i % 2 == 0 else 1
            if fp == 0:
                names = ("AgentA", "AgentB")
            else:
                names = ("AgentB", "AgentA")

            if i < 60:
                # A wins
                w = 0 if fp == 0 else 1
            else:
                # B wins
                w = 1 if fp == 0 else 0
            games.append(_make_game(i, (10, 5), winner=w,
                                    first_player=fp, agent_names=names))

        m = _make_matchup(games)
        rate, ci_lo, ci_hi = win_rate_with_ci(m)
        assert abs(rate - 0.6) < 0.001
        assert ci_lo < 0.6
        assert ci_hi > 0.6

    def test_win_rate_excludes_ties(self):
        # 3 A wins, 2 B wins, 5 ties -> rate = 3/5 = 0.6
        games = []
        for i in range(10):
            fp = 0 if i % 2 == 0 else 1
            names = ("AgentA", "AgentB") if fp == 0 else ("AgentB", "AgentA")
            if i < 3:
                w = 0 if fp == 0 else 1  # A wins
            elif i < 5:
                w = 1 if fp == 0 else 0  # B wins
            else:
                w = None  # tie
            games.append(_make_game(i, (8, 8) if w is None else (10, 5),
                                    winner=w, first_player=fp,
                                    agent_names=names))

        m = _make_matchup(games)
        rate, _, _ = win_rate_with_ci(m)
        assert abs(rate - 0.6) < 0.001

    def test_mean_scores_basic(self):
        games = [
            # game 0: A=seat0 scores (10, 5) -> A=10, B=5
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            # game 1: B=seat0 scores (3, 12) -> A=12, B=3
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        m = _make_matchup(games)
        a_mean, b_mean = mean_scores(m)
        assert abs(a_mean - 11.0) < 0.001  # (10+12)/2
        assert abs(b_mean - 4.0) < 0.001   # (5+3)/2

    def test_score_std_dev(self):
        # A scores: 10, 12 -> mean=11, var=(1+1)/1=2, std=sqrt(2)
        games = [
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        m = _make_matchup(games)
        a_std, b_std = score_std_dev(m)
        assert abs(a_std - math.sqrt(2)) < 0.001
        # B scores: 5, 3 -> mean=4, var=(1+1)/1=2, std=sqrt(2)
        assert abs(b_std - math.sqrt(2)) < 0.001

    def test_coefficient_of_variation(self):
        games = [
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        m = _make_matchup(games)
        a_cv, b_cv = coefficient_of_variation(m)
        # A: std=sqrt(2), mean=11 -> CV = sqrt(2)/11
        assert abs(a_cv - math.sqrt(2) / 11) < 0.001
        # B: std=sqrt(2), mean=4 -> CV = sqrt(2)/4
        assert abs(b_cv - math.sqrt(2) / 4) < 0.001

    def test_mean_score_advantage(self):
        games = [
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(1, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        m = _make_matchup(games)
        adv = mean_score_advantage(m)
        assert abs(adv - 7.0) < 0.001  # 11 - 4

    def test_t_test_significant(self):
        # 20 games where A always beats B by 5 points
        games = []
        for i in range(20):
            fp = 0 if i % 2 == 0 else 1
            names = ("AgentA", "AgentB") if fp == 0 else ("AgentB", "AgentA")
            if fp == 0:
                scores = (15, 10)
            else:
                scores = (10, 15)
            games.append(_make_game(i, scores, winner=0 if fp == 0 else 1,
                                    first_player=fp, agent_names=names))
        m = _make_matchup(games)
        t_stat, p_val = t_test_scores(m)
        # All diffs = +5, zero variance in diffs -> infinite t, p=0
        assert p_val < 0.05

    def test_t_test_not_significant(self):
        # 20 games with identical scores
        games = []
        for i in range(20):
            fp = 0 if i % 2 == 0 else 1
            names = ("AgentA", "AgentB") if fp == 0 else ("AgentB", "AgentA")
            games.append(_make_game(i, (10, 10), winner=None,
                                    first_player=fp, agent_names=names))
        m = _make_matchup(games)
        t_stat, p_val = t_test_scores(m)
        assert abs(t_stat) < 0.001
        assert p_val > 0.95

    def test_first_player_win_rate(self):
        # 6 decisive games, seat 0 wins 4 of them
        games = [
            _make_game(0, (10, 5), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(1, (11, 6), winner=0, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            _make_game(2, (9, 4), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(3, (3, 12), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
            _make_game(4, (7, 2), winner=0, first_player=0,
                       agent_names=("AgentA", "AgentB")),
            _make_game(5, (2, 14), winner=1, first_player=1,
                       agent_names=("AgentB", "AgentA")),
        ]
        m = _make_matchup(games)
        rate = first_player_win_rate(m)
        # Seat 0 wins: games 0, 1, 2, 4 = 4 out of 6
        assert abs(rate - 4 / 6) < 0.001


# ===========================================================================
# TestEndToEnd
# ===========================================================================

class TestEndToEnd:

    def test_full_pipeline(self):
        """Runner -> CSV -> load -> analysis -> summary_text."""
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=20,
            base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            save_results_csv(result, path)
            loaded = load_results_csv(path)

            assert len(loaded.games) == 20
            for orig, ldg in zip(result.games, loaded.games):
                assert orig.scores == ldg.scores
                assert orig.winner == ldg.winner

            text = summary_text(loaded)
            assert "RandomAgent" in text
            assert "Win rate" in text
            assert "Paired t-test" in text
        finally:
            os.unlink(path)

    def test_mirror_matchup(self):
        """Random vs Random: win rate should be roughly 50%."""
        runner = SimulationRunner(
            "RandomAgent", "RandomAgent", num_games=200,
            base_seed=42, fast_mode=True, num_workers=1,
        )
        result = runner.run()

        rate, ci_lo, ci_hi = win_rate_with_ci(result)
        # Should be between 20% and 80% (very loose for small N)
        assert 0.20 <= rate <= 0.80

        adv = mean_score_advantage(result)
        # Score advantage should be small (< 3 coins)
        assert abs(adv) < 3.0
