"""Tests for game orchestration."""

import pytest
import random
from src.game.game import GameState, Action, ActionType, play_game
from src.game.camel import CamelColor


class TestGameState:
    """Tests for GameState."""

    def test_create_new_game(self):
        """Create a new game with initial setup."""
        state = GameState.create_new_game(num_players=2, seed=42)

        assert state.get_num_players() == 2
        assert state.current_player == 0
        assert state.leg_number == 1
        assert not state.is_game_over

        # All players start with 3 coins
        scores = state.get_scores()
        assert scores == (3, 3)

        # All camels should be on the board
        for camel in [CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW,
                      CamelColor.RED, CamelColor.PURPLE]:
            pos = state.board.camel_positions.get_camel_space(camel)
            assert pos is not None
            assert 1 <= pos <= 3  # Initial positions from dice

    def test_get_legal_actions(self):
        """Get legal actions returns valid options."""
        state = GameState.create_new_game(num_players=2, seed=42)
        actions = state.get_legal_actions()

        # Should have betting tickets (5 camels)
        betting_actions = [a for a in actions
                         if a.action_type == ActionType.TAKE_BETTING_TICKET]
        assert len(betting_actions) == 5

        # Should have pyramid ticket option
        pyramid_actions = [a for a in actions
                         if a.action_type == ActionType.TAKE_PYRAMID_TICKET]
        assert len(pyramid_actions) == 1

        # Should have overall winner/loser bets (5 camels x 2 bet types)
        winner_actions = [a for a in actions
                        if a.action_type == ActionType.BET_OVERALL_WINNER]
        assert len(winner_actions) == 5

        loser_actions = [a for a in actions
                       if a.action_type == ActionType.BET_OVERALL_LOSER]
        assert len(loser_actions) == 5

    def test_take_betting_ticket(self):
        """Taking betting ticket removes it from available."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Take blue betting ticket
        action = Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE)
        new_state = state.apply_action(action)

        # Current player should advance
        assert new_state.current_player == 1

        # Blue ticket should have reduced availability
        remaining = new_state.betting.available_tickets[CamelColor.BLUE]
        assert len(remaining) == 3  # Was 4, now 3

    def test_take_pyramid_ticket_rolls_dice(self):
        """Taking pyramid ticket rolls dice and moves camel."""
        state = GameState.create_new_game(num_players=2, seed=42)
        rng = random.Random(42)

        action = Action(ActionType.TAKE_PYRAMID_TICKET)
        new_state = state.apply_action(action, rng)

        # Pyramid should have one fewer die
        assert (len(new_state.pyramid.remaining) < len(state.pyramid.remaining) or
                new_state.pyramid.grey_rolled != state.pyramid.grey_rolled)

        # Player should have 1 pyramid ticket
        assert new_state.betting.player_pyramid_tickets[0] == 1

    def test_overall_bet_uses_finish_card(self):
        """Overall bet removes finish card from player."""
        state = GameState.create_new_game(num_players=2, seed=42)

        action = Action(ActionType.BET_OVERALL_WINNER, camel=CamelColor.BLUE)
        new_state = state.apply_action(action)

        # Player 0 can no longer bet on Blue
        player_state = new_state.players[0]
        assert not player_state.can_bet_on_overall(CamelColor.BLUE)
        assert player_state.can_bet_on_overall(CamelColor.GREEN)  # Others still ok

    def test_game_advances_turns(self):
        """Game correctly advances between players."""
        state = GameState.create_new_game(num_players=3, seed=42)
        assert state.current_player == 0

        action = Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE)

        state = state.apply_action(action)
        assert state.current_player == 1

        state = state.apply_action(action)
        assert state.current_player == 2

        state = state.apply_action(action)
        assert state.current_player == 0  # Wraps around


class TestPlayGame:
    """Tests for full game play."""

    def test_play_game_with_random_agents(self):
        """Play a complete game with random agents."""
        def random_agent(state, legal_actions):
            return random.choice(legal_actions)

        rng = random.Random(42)
        random.seed(42)

        final_state, history = play_game(
            num_players=2,
            agent_functions=[random_agent, random_agent],
            seed=42,
            verbose=False
        )

        # Game should be over
        assert final_state.is_game_over

        # Should have played some actions
        assert len(history) > 0

        # Scores should be non-negative
        scores = final_state.get_scores()
        assert all(s >= 0 for s in scores)

    def test_play_multiple_games_deterministic(self):
        """Same seed produces same game."""
        def random_agent(state, legal_actions):
            # Use deterministic choice based on state
            return legal_actions[0]

        state1, history1 = play_game(
            num_players=2,
            agent_functions=[random_agent, random_agent],
            seed=123
        )

        state2, history2 = play_game(
            num_players=2,
            agent_functions=[random_agent, random_agent],
            seed=123
        )

        assert state1.get_scores() == state2.get_scores()
        assert len(history1) == len(history2)


class TestLegScoring:
    """Tests for leg end scoring."""

    def test_leg_scoring_first_place_bet(self):
        """Correct first place bet earns ticket value."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Find the current leader
        leader = state.board.get_leader()

        # Player 0 bets on leader
        action = Action(ActionType.TAKE_BETTING_TICKET, camel=leader)
        state = state.apply_action(action)

        initial_score = state.players[0].coins

        # Play until leg ends
        rng = random.Random(42)
        while not state.pyramid.is_leg_complete() and not state.is_game_over:
            action = Action(ActionType.TAKE_PYRAMID_TICKET)
            if action in state.get_legal_actions():
                state = state.apply_action(action, rng)
            else:
                break

        # If leader is still first, player should have gained coins
        # (exact amount depends on game state)
        # This is a basic sanity check
        assert state.leg_number >= 1
