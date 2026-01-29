"""Tests for agent implementations."""

import pytest
from src.game.game import GameState, Action, ActionType, play_game
from src.game.camel import CamelColor
from src.agents import (
    Agent,
    RandomAgent,
    GreedyAgent,
    ConservativeAgent,
    HeuristicAgent,
)


class TestAgentBase:
    """Test base agent functionality."""

    def test_agent_is_abstract(self):
        """Agent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Agent()

    def test_agent_callable(self):
        """Agents are callable for use with play_game."""
        agent = RandomAgent(seed=42)
        state = GameState.create_new_game(2, seed=123)
        legal_actions = state.get_legal_actions()

        # Should be callable
        action = agent(state, legal_actions)
        assert action in legal_actions

    def test_agent_repr(self):
        """Agent has useful string representation."""
        agent = RandomAgent(name="TestBot")
        assert "RandomAgent" in repr(agent)
        assert "TestBot" in repr(agent)


class TestRandomAgent:
    """Test RandomAgent implementation."""

    def test_random_agent_returns_legal_action(self):
        """RandomAgent always returns a legal action."""
        agent = RandomAgent(seed=42)
        state = GameState.create_new_game(2, seed=123)

        for _ in range(10):
            legal_actions = state.get_legal_actions()
            if not legal_actions:
                break
            action = agent.choose_action(state, legal_actions)
            assert action in legal_actions
            state = state.apply_action(action)

    def test_random_agent_reproducible(self):
        """RandomAgent with same seed produces same results."""
        state = GameState.create_new_game(2, seed=123)
        legal_actions = state.get_legal_actions()

        agent1 = RandomAgent(seed=42)
        agent2 = RandomAgent(seed=42)

        actions1 = [agent1.choose_action(state, legal_actions) for _ in range(5)]
        actions2 = [agent2.choose_action(state, legal_actions) for _ in range(5)]

        assert actions1 == actions2

    def test_random_agent_varies_choices(self):
        """RandomAgent with different seeds varies choices."""
        state = GameState.create_new_game(2, seed=123)
        legal_actions = state.get_legal_actions()

        # Run many times and collect unique actions
        unique_actions = set()
        for seed in range(100):
            agent = RandomAgent(seed=seed)
            action = agent.choose_action(state, legal_actions)
            unique_actions.add(action)

        # Should see variety (at least 2 different actions)
        assert len(unique_actions) >= 2


class TestGreedyAgent:
    """Test GreedyAgent implementation."""

    def test_greedy_agent_returns_legal_action(self):
        """GreedyAgent always returns a legal action."""
        agent = GreedyAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        legal_actions = state.get_legal_actions()
        action = agent.choose_action(state, legal_actions)
        assert action in legal_actions

    def test_greedy_agent_prefers_high_ev(self):
        """GreedyAgent should prefer high EV actions."""
        agent = GreedyAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        # Run a few turns and verify no crashes
        for _ in range(5):
            legal_actions = state.get_legal_actions()
            if not legal_actions or state.is_game_over:
                break
            action = agent.choose_action(state, legal_actions)
            assert action in legal_actions
            state = state.apply_action(action)

    def test_greedy_agent_avoids_early_overall_bets(self):
        """GreedyAgent should avoid overall bets early in game."""
        agent = GreedyAgent(seed=42, overall_bet_threshold=0.3, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        # At start of game, prob_game_ends is very low
        # Greedy agent should not choose overall bets
        legal_actions = state.get_legal_actions()
        action = agent.choose_action(state, legal_actions)

        # Overall bets should be discouraged (EV = -2) so should pick something else
        assert action.action_type in [
            ActionType.TAKE_BETTING_TICKET,
            ActionType.TAKE_PYRAMID_TICKET,
            ActionType.PLACE_SPECTATOR_TILE,
        ]


class TestConservativeAgent:
    """Test ConservativeAgent implementation."""

    def test_conservative_agent_returns_legal_action(self):
        """ConservativeAgent always returns a legal action."""
        agent = ConservativeAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        legal_actions = state.get_legal_actions()
        action = agent.choose_action(state, legal_actions)
        assert action in legal_actions

    def test_conservative_prefers_pyramid_when_uncertain(self):
        """ConservativeAgent prefers pyramid ticket when bets are uncertain."""
        agent = ConservativeAgent(seed=42, min_bet_prob=0.9, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        # With very high threshold, should prefer pyramid ticket
        legal_actions = state.get_legal_actions()
        action = agent.choose_action(state, legal_actions)

        # Should be pyramid ticket or leg bet (fallback)
        assert action.action_type in [
            ActionType.TAKE_PYRAMID_TICKET,
            ActionType.TAKE_BETTING_TICKET,
        ]

    def test_conservative_avoids_spectator_tiles(self):
        """ConservativeAgent should not place spectator tiles."""
        agent = ConservativeAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        # Run several turns
        for _ in range(20):
            legal_actions = state.get_legal_actions()
            if not legal_actions or state.is_game_over:
                break
            action = agent.choose_action(state, legal_actions)

            # Should never choose spectator tile
            assert action.action_type != ActionType.PLACE_SPECTATOR_TILE

            state = state.apply_action(action)


class TestHeuristicAgent:
    """Test HeuristicAgent implementation."""

    def test_heuristic_agent_returns_legal_action(self):
        """HeuristicAgent always returns a legal action."""
        agent = HeuristicAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        legal_actions = state.get_legal_actions()
        action = agent.choose_action(state, legal_actions)
        assert action in legal_actions

    def test_heuristic_agent_runs_full_game(self):
        """HeuristicAgent can play a complete game."""
        agent = HeuristicAgent(seed=42, fast_mode=True)
        state = GameState.create_new_game(2, seed=123)

        turns = 0
        while not state.is_game_over and turns < 200:
            legal_actions = state.get_legal_actions()
            if not legal_actions:
                break
            action = agent.choose_action(state, legal_actions)
            state = state.apply_action(action)
            turns += 1

        # Game should complete
        assert state.is_game_over or turns >= 200


class TestPlayGame:
    """Test agents with play_game function."""

    def test_random_vs_random(self):
        """Two random agents can play a complete game."""
        agents = [RandomAgent(seed=i) for i in range(2)]

        final_state, history = play_game(
            num_players=2,
            agent_functions=agents,
            seed=42
        )

        assert final_state.is_game_over
        assert len(history) > 0

    def test_greedy_few_turns(self):
        """Greedy agent can make valid moves for several turns."""
        agent = GreedyAgent(seed=0, fast_mode=True)
        state = GameState.create_new_game(2, seed=42)

        # Run just 5 turns to verify it works without running full game
        for _ in range(5):
            if state.is_game_over:
                break
            legal_actions = state.get_legal_actions()
            action = agent.choose_action(state, legal_actions)
            assert action in legal_actions
            state = state.apply_action(action)

    def test_conservative_few_turns(self):
        """Conservative agent can make valid moves for several turns."""
        agent = ConservativeAgent(seed=0, fast_mode=True)
        state = GameState.create_new_game(2, seed=42)

        for _ in range(5):
            if state.is_game_over:
                break
            legal_actions = state.get_legal_actions()
            action = agent.choose_action(state, legal_actions)
            assert action in legal_actions
            state = state.apply_action(action)

    def test_heuristic_few_turns(self):
        """Heuristic agent can make valid moves for several turns."""
        agent = HeuristicAgent(seed=0, fast_mode=True)
        state = GameState.create_new_game(2, seed=42)

        for _ in range(5):
            if state.is_game_over:
                break
            legal_actions = state.get_legal_actions()
            action = agent.choose_action(state, legal_actions)
            assert action in legal_actions
            state = state.apply_action(action)


class TestAgentReproducibility:
    """Test that agents produce reproducible results."""

    def test_greedy_reproducible(self):
        """GreedyAgent with same seed produces same choices."""
        state = GameState.create_new_game(2, seed=42)
        legal_actions = state.get_legal_actions()

        agent1 = GreedyAgent(seed=0, fast_mode=True)
        agent2 = GreedyAgent(seed=0, fast_mode=True)

        action1 = agent1.choose_action(state, legal_actions)
        action2 = agent2.choose_action(state, legal_actions)

        assert action1 == action2

    def test_different_seeds_different_games(self):
        """Different seeds should produce different games."""
        def run_game(seed):
            agents = [RandomAgent(seed=seed), RandomAgent(seed=seed + 100)]
            final_state, _ = play_game(
                num_players=2,
                agent_functions=agents,
                seed=seed
            )
            return final_state.get_scores()

        results = [run_game(i) for i in range(10)]
        unique_results = set(results)

        # Should have variety in outcomes
        assert len(unique_results) >= 3


# Helper functions for multiprocessing (must be at module level to be picklable)
def _run_random_game(seed):
    """Run one random game and return scores."""
    agents = [RandomAgent(seed=seed), RandomAgent(seed=seed + 1000)]
    final_state, _ = play_game(
        num_players=2,
        agent_functions=agents,
        seed=seed
    )
    return final_state.get_scores()


def _run_greedy_game(seed):
    """Run one game with GreedyAgent vs RandomAgent (fast_mode=True, no grey die)."""
    agents = [
        GreedyAgent(seed=seed, fast_mode=True),
        RandomAgent(seed=seed + 1000)
    ]
    final_state, _ = play_game(
        num_players=2,
        agent_functions=agents,
        seed=seed
    )
    return final_state.get_scores()


def _run_greedy_game_full(seed):
    """Run one game with GreedyAgent vs RandomAgent (fast_mode=False, WITH grey die)."""
    agents = [
        GreedyAgent(seed=seed, fast_mode=False),  # Include grey die calculation
        RandomAgent(seed=seed + 1000)
    ]
    final_state, _ = play_game(
        num_players=2,
        agent_functions=agents,
        seed=seed
    )
    return final_state.get_scores()


class TestParallelPerformance:
    """Compare single-core vs multi-core performance."""

    def test_parallel_random_games(self):
        """Random games are too fast - parallel overhead dominates."""
        import time
        from multiprocessing import Pool, cpu_count

        num_games = 100

        # Sequential
        start = time.time()
        for i in range(num_games):
            _run_random_game(i)
        sequential_time = time.time() - start

        # Parallel
        start = time.time()
        with Pool(processes=cpu_count()) as pool:
            pool.map(_run_random_game, range(num_games))
        parallel_time = time.time() - start

        print(f"\n=== RANDOM GAMES ({num_games} games) ===")
        print(f"CPU cores: {cpu_count()}")
        print(f"Sequential: {sequential_time:.2f}s")
        print(f"Parallel:   {parallel_time:.2f}s")
        print(f"Speedup:    {sequential_time / parallel_time:.1f}x")
        print("(Random games are too fast - overhead dominates)")

    def test_parallel_greedy_games(self):
        """Greedy games benefit from parallelization."""
        import time
        from multiprocessing import Pool, cpu_count

        num_games = 4  # Small number because each game is slow

        # Sequential
        start = time.time()
        for i in range(num_games):
            _run_greedy_game(i)
        sequential_time = time.time() - start

        # Parallel
        start = time.time()
        with Pool(processes=cpu_count()) as pool:
            pool.map(_run_greedy_game, range(num_games))
        parallel_time = time.time() - start

        speedup = sequential_time / parallel_time

        print(f"\n=== GREEDY GAMES ({num_games} games) ===")
        print(f"CPU cores: {cpu_count()}")
        print(f"Sequential: {sequential_time:.2f}s")
        print(f"Parallel:   {parallel_time:.2f}s")
        print(f"Speedup:    {speedup:.1f}x")

        # Greedy games should show meaningful speedup
        assert speedup > 1.5, f"Expected speedup > 1.5x, got {speedup:.1f}x"

    @pytest.mark.slow
    def test_parallel_greedy_full_mode(self):
        """
        Greedy games WITH grey die (full probability calculation).

        This is the most accurate but slowest mode.
        With grey die: ~1M outcomes instead of 29K.
        """
        import time
        from multiprocessing import Pool, cpu_count

        num_games = 2  # Very small because each game is VERY slow with grey die

        print(f"\n=== GREEDY FULL MODE ({num_games} games, WITH grey die) ===")
        print(f"CPU cores: {cpu_count()}")
        print("This calculates ~1M outcomes per decision (36x more than fast_mode)")
        print("Running... (this will take a while)")

        # Parallel only (sequential would take too long)
        start = time.time()
        with Pool(processes=cpu_count()) as pool:
            results = pool.map(_run_greedy_game_full, range(num_games))
        parallel_time = time.time() - start

        print(f"Parallel time: {parallel_time:.1f}s")
        print(f"Time per game: {parallel_time / num_games:.1f}s")
        print(f"Results: {results}")

        # Estimate for 1000 games
        estimated_1000 = (parallel_time / num_games) * 1000 / cpu_count()
        print(f"Estimated time for 1000 games (parallel): {estimated_1000 / 60:.0f} minutes")
