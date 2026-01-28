"""Tests for game flow mechanics (turns, legs, game end)."""

import pytest
import random
from src.game.game import GameState, Action, ActionType, play_game
from src.game.camel import CamelColor
from src.game.dice import Pyramid, DieColor


class TestTurnStructure:
    """Tests for turn mechanics."""

    def test_one_action_per_turn(self):
        """Player takes exactly one action per turn."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Take one action
        action = Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE)
        new_state = state.apply_action(action)

        # Turn should have advanced
        assert new_state.current_player != state.current_player

    def test_four_action_types_available(self):
        """Four types of actions are available."""
        state = GameState.create_new_game(num_players=2, seed=42)
        actions = state.get_legal_actions()

        action_types = set(a.action_type for a in actions)

        assert ActionType.TAKE_BETTING_TICKET in action_types
        assert ActionType.TAKE_PYRAMID_TICKET in action_types
        assert ActionType.BET_OVERALL_WINNER in action_types
        assert ActionType.BET_OVERALL_LOSER in action_types
        # PLACE_SPECTATOR_TILE may or may not be available depending on board state

    def test_turn_passes_clockwise(self):
        """Turns pass to the next player in order."""
        state = GameState.create_new_game(num_players=4, seed=42)

        action = Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE)

        assert state.current_player == 0
        state = state.apply_action(action)
        assert state.current_player == 1
        state = state.apply_action(action)
        assert state.current_player == 2
        state = state.apply_action(action)
        assert state.current_player == 3
        state = state.apply_action(action)
        assert state.current_player == 0  # Wraps back

    def test_no_actions_when_game_over(self):
        """No legal actions when game is over."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Manually set game as over
        state = GameState(
            board=state.board,
            pyramid=state.pyramid,
            betting=state.betting,
            players=state.players,
            current_player=state.current_player,
            leg_number=state.leg_number,
            is_game_over=True,
            rng_state=state.rng_state
        )

        actions = state.get_legal_actions()
        assert len(actions) == 0


class TestLegMechanics:
    """Tests for leg mechanics."""

    def test_leg_ends_when_five_dice_revealed(self):
        """Leg ends when 5 of 6 dice have been revealed."""
        pyramid = Pyramid()

        # Roll 4 dice - leg not complete
        for _ in range(4):
            rng = random.Random()
            pyramid, _ = pyramid.roll_from_pyramid(rng)

        assert not pyramid.is_leg_complete()

        # Roll 5th die - leg complete (1 remains)
        pyramid, _ = pyramid.roll_from_pyramid(random.Random())
        assert pyramid.is_leg_complete()

    def test_pyramid_refilled_after_leg(self):
        """Pyramid is refilled with all dice after leg ends."""
        state = GameState.create_new_game(num_players=2, seed=42)
        rng = random.Random(42)

        # Roll dice until leg ends
        while not state.pyramid.is_leg_complete() and not state.is_game_over:
            action = Action(ActionType.TAKE_PYRAMID_TICKET)
            if action in state.get_legal_actions():
                state = state.apply_action(action, rng)
            else:
                break

        # If not game over, pyramid should be refilled
        if not state.is_game_over:
            assert len(state.pyramid.remaining) == 5
            assert not state.pyramid.grey_rolled

    def test_leg_number_increments(self):
        """Leg number increments after each leg."""
        state = GameState.create_new_game(num_players=2, seed=42)
        rng = random.Random(42)

        assert state.leg_number == 1

        # Play until leg ends (but not game over)
        initial_leg = state.leg_number
        while state.leg_number == initial_leg and not state.is_game_over:
            action = Action(ActionType.TAKE_PYRAMID_TICKET)
            if action in state.get_legal_actions():
                state = state.apply_action(action, rng)
            else:
                # Take any action to progress
                actions = state.get_legal_actions()
                if actions:
                    state = state.apply_action(actions[0], rng)
                else:
                    break

        if not state.is_game_over:
            assert state.leg_number == 2

    def test_betting_tickets_returned_after_leg(self):
        """Betting tickets return to stacks after leg scoring."""
        state = GameState.create_new_game(num_players=2, seed=42)
        rng = random.Random(42)

        # Take some betting tickets
        state = state.apply_action(
            Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE), rng
        )
        state = state.apply_action(
            Action(ActionType.TAKE_BETTING_TICKET, camel=CamelColor.BLUE), rng
        )

        # Play until leg ends
        initial_leg = state.leg_number
        while state.leg_number == initial_leg and not state.is_game_over:
            action = Action(ActionType.TAKE_PYRAMID_TICKET)
            if action in state.get_legal_actions():
                state = state.apply_action(action, rng)
            else:
                actions = state.get_legal_actions()
                if actions:
                    state = state.apply_action(actions[0], rng)
                else:
                    break

        # After leg, all tickets should be back
        if not state.is_game_over:
            assert len(state.betting.available_tickets[CamelColor.BLUE]) == 4

    def test_spectator_tiles_returned_after_leg(self):
        """Spectator tiles return to owners after leg ends."""
        state = GameState.create_new_game(num_players=2, seed=42)
        rng = random.Random(42)

        # Find a valid place for spectator tile
        valid_spaces = state.board.get_valid_spectator_spaces(0)
        if valid_spaces:
            action = Action(
                ActionType.PLACE_SPECTATOR_TILE,
                space=valid_spaces[0],
                is_cheering=True
            )
            state = state.apply_action(action, rng)

            # Player 0 should not have tile anymore
            assert not state.players[0].has_spectator_tile

            # Play until leg ends
            initial_leg = state.leg_number
            while state.leg_number == initial_leg and not state.is_game_over:
                action = Action(ActionType.TAKE_PYRAMID_TICKET)
                if action in state.get_legal_actions():
                    state = state.apply_action(action, rng)
                else:
                    actions = state.get_legal_actions()
                    if actions:
                        state = state.apply_action(actions[0], rng)
                    else:
                        break

            # After leg, player should have tile back
            if not state.is_game_over:
                assert state.players[0].has_spectator_tile

    def test_starting_player_rule(self):
        """Starting player after leg = player left of last pyramid ticket taker."""
        state = GameState.create_new_game(num_players=4, seed=42)
        rng = random.Random(42)

        # Track who takes the last pyramid ticket
        initial_leg = state.leg_number
        last_pyramid_player = None

        while state.leg_number == initial_leg and not state.is_game_over:
            action = Action(ActionType.TAKE_PYRAMID_TICKET)
            if action in state.get_legal_actions():
                last_pyramid_player = state.current_player
                state = state.apply_action(action, rng)
            else:
                # Take any other action to progress
                actions = state.get_legal_actions()
                if actions:
                    state = state.apply_action(actions[0], rng)
                else:
                    break

        # If leg ended (not game over), check starting player
        if not state.is_game_over and last_pyramid_player is not None:
            # Starting player should be to the left (next player) of last pyramid taker
            expected_starting_player = (last_pyramid_player + 1) % 4
            assert state.current_player == expected_starting_player


class TestGameEnd:
    """Tests for game end mechanics."""

    def test_game_ends_when_camel_finishes(self):
        """Game ends immediately when any camel crosses finish line."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # The game should eventually end
        def random_agent(state, actions):
            return random.choice(actions)

        random.seed(42)
        final_state, _ = play_game(
            num_players=2,
            agent_functions=[random_agent, random_agent],
            seed=42
        )

        assert final_state.is_game_over
        assert final_state.board.is_game_over()

    def test_most_coins_wins(self):
        """Player with most coins at game end wins."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Manually give player 0 more coins
        from src.game.betting import PlayerState
        players = list(state.players)
        players[0] = players[0].add_coins(10)
        players[1] = players[1].add_coins(5)

        state = GameState(
            board=state.board,
            pyramid=state.pyramid,
            betting=state.betting,
            players=tuple(players),
            current_player=0,
            leg_number=1,
            is_game_over=True,
            rng_state=None
        )

        winner = state.get_winner()
        assert winner == 0  # Player 0 has more coins

    def test_tie_returns_none(self):
        """Tied game returns None for winner."""
        state = GameState.create_new_game(num_players=2, seed=42)

        # Give both players equal coins
        from src.game.betting import PlayerState
        players = list(state.players)
        players[0] = PlayerState(coins=10, has_spectator_tile=True, available_finish_cards=())
        players[1] = PlayerState(coins=10, has_spectator_tile=True, available_finish_cards=())

        state = GameState(
            board=state.board,
            pyramid=state.pyramid,
            betting=state.betting,
            players=tuple(players),
            current_player=0,
            leg_number=1,
            is_game_over=True,
            rng_state=None
        )

        winner = state.get_winner()
        assert winner is None  # Tie

    def test_get_scores(self):
        """get_scores returns correct coin counts."""
        state = GameState.create_new_game(num_players=3, seed=42)

        scores = state.get_scores()
        assert len(scores) == 3
        assert all(s == 3 for s in scores)  # All start with 3


class TestFullGame:
    """Integration tests for full game play."""

    def test_complete_game_runs(self):
        """A complete game can run without errors."""
        def random_agent(state, actions):
            return random.choice(actions)

        random.seed(123)
        final_state, history = play_game(
            num_players=2,
            agent_functions=[random_agent, random_agent],
            seed=123
        )

        assert final_state.is_game_over
        assert len(history) > 0

    def test_game_deterministic_with_seed(self):
        """Same seed produces same game outcome."""
        def first_action_agent(state, actions):
            return actions[0]

        state1, history1 = play_game(
            num_players=2,
            agent_functions=[first_action_agent, first_action_agent],
            seed=456
        )

        state2, history2 = play_game(
            num_players=2,
            agent_functions=[first_action_agent, first_action_agent],
            seed=456
        )

        assert state1.get_scores() == state2.get_scores()
        assert len(history1) == len(history2)

    def test_multiple_legs_can_occur(self):
        """Games can have multiple legs before finishing."""
        def random_agent(state, actions):
            return random.choice(actions)

        # Run many games and check if any have multiple legs
        multi_leg_found = False
        for seed in range(100):
            random.seed(seed)
            final_state, _ = play_game(
                num_players=2,
                agent_functions=[random_agent, random_agent],
                seed=seed
            )
            if final_state.leg_number > 1:
                multi_leg_found = True
                break

        assert multi_leg_found, "No multi-leg games found in 100 attempts"

    def test_three_player_game(self):
        """Three-player game works correctly."""
        def random_agent(state, actions):
            return random.choice(actions)

        random.seed(789)
        final_state, history = play_game(
            num_players=3,
            agent_functions=[random_agent, random_agent, random_agent],
            seed=789
        )

        assert final_state.is_game_over
        assert len(final_state.get_scores()) == 3

    def test_four_player_game(self):
        """Four-player game works correctly."""
        def random_agent(state, actions):
            return random.choice(actions)

        random.seed(999)
        final_state, history = play_game(
            num_players=4,
            agent_functions=[random_agent] * 4,
            seed=999
        )

        assert final_state.is_game_over
        assert len(final_state.get_scores()) == 4
