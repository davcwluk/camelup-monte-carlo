"""Tests for camel movement mechanics."""

import pytest
from src.game.camel import CamelColor, CamelPositions, CamelStack, RACING_CAMELS
from src.game.board import Board, TRACK_LENGTH, FINISH_LINE


class TestBasicMovement:
    """Tests for basic camel movement."""

    def test_racing_camel_moves_forward(self):
        """Racing camels move forward (increasing space numbers)."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)

        # Move forward 2 spaces
        positions = positions.move_camel(CamelColor.BLUE, 2)

        assert positions.get_camel_space(CamelColor.BLUE) == 5

    def test_camel_moves_exact_spaces(self):
        """Camel moves exactly the number of spaces specified."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 1)

        positions = positions.move_camel(CamelColor.BLUE, 1)
        assert positions.get_camel_space(CamelColor.BLUE) == 2

        positions = positions.move_camel(CamelColor.BLUE, 2)
        assert positions.get_camel_space(CamelColor.BLUE) == 4

        positions = positions.move_camel(CamelColor.BLUE, 3)
        assert positions.get_camel_space(CamelColor.BLUE) == 7

    def test_camel_finishes_race(self):
        """Camel crossing space 16 is considered finished."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 15)

        # Move 3 spaces (15 -> 18, past finish line at 17)
        positions = positions.move_camel(CamelColor.BLUE, 3)

        assert positions.get_camel_space(CamelColor.BLUE) == 18
        assert positions.is_camel_finished(CamelColor.BLUE, FINISH_LINE)

    def test_any_camel_finished_detection(self):
        """Detect when any racing camel has finished."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 10)
        positions = positions.place_camel(CamelColor.GREEN, 15)

        assert not positions.any_camel_finished(FINISH_LINE)

        # Green finishes
        positions = positions.move_camel(CamelColor.GREEN, 3)
        assert positions.any_camel_finished(FINISH_LINE)


class TestStackingMovement:
    """Tests for camel stacking during movement."""

    def test_camels_form_stack(self):
        """Camels landing on same space form a stack."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 5)
        positions = positions.place_camel(CamelColor.GREEN, 5)

        stack = positions.get_stack(5)
        assert len(stack) == 2
        assert CamelColor.BLUE in stack
        assert CamelColor.GREEN in stack

    def test_camel_lands_on_top(self):
        """Camel moving to occupied space lands ON TOP."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.RED, 5)
        positions = positions.place_camel(CamelColor.BLUE, 3)

        # Blue moves to space 5 (where Red is)
        positions = positions.move_camel(CamelColor.BLUE, 2)

        stack = positions.get_stack(5)
        assert stack.bottom() == CamelColor.RED
        assert stack.top() == CamelColor.BLUE

    def test_moving_camel_carries_stack(self):
        """Moving camel carries all camels above it."""
        positions = CamelPositions.create_empty()
        # Stack at space 3: Blue (bottom), Green (middle), Yellow (top)
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 3)
        positions = positions.place_camel(CamelColor.YELLOW, 3)

        # Move Blue - should carry Green and Yellow
        positions = positions.move_camel(CamelColor.BLUE, 2)

        # All three should be at space 5
        assert positions.get_camel_space(CamelColor.BLUE) == 5
        assert positions.get_camel_space(CamelColor.GREEN) == 5
        assert positions.get_camel_space(CamelColor.YELLOW) == 5

        # Stack order preserved
        stack = positions.get_stack(5)
        assert stack.camels == (CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW)

    def test_camels_below_stay_in_place(self):
        """Camels below the moving camel stay where they are."""
        positions = CamelPositions.create_empty()
        # Stack at space 3: Blue (bottom), Green (middle), Yellow (top)
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 3)
        positions = positions.place_camel(CamelColor.YELLOW, 3)

        # Move Green - should carry only Yellow, leave Blue
        positions = positions.move_camel(CamelColor.GREEN, 2)

        # Blue stays at space 3
        assert positions.get_camel_space(CamelColor.BLUE) == 3
        # Green and Yellow at space 5
        assert positions.get_camel_space(CamelColor.GREEN) == 5
        assert positions.get_camel_space(CamelColor.YELLOW) == 5

        # Stack at space 3 only has Blue
        stack_3 = positions.get_stack(3)
        assert stack_3.camels == (CamelColor.BLUE,)

        # Stack at space 5 has Green (bottom), Yellow (top)
        stack_5 = positions.get_stack(5)
        assert stack_5.camels == (CamelColor.GREEN, CamelColor.YELLOW)

    def test_stack_lands_on_existing_stack(self):
        """Moving stack lands on top of existing stack."""
        positions = CamelPositions.create_empty()
        # Stack at space 5: Red (bottom), Purple (top)
        positions = positions.place_camel(CamelColor.RED, 5)
        positions = positions.place_camel(CamelColor.PURPLE, 5)
        # Stack at space 3: Blue (bottom), Green (top)
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 3)

        # Move Blue stack to space 5
        positions = positions.move_camel(CamelColor.BLUE, 2)

        stack = positions.get_stack(5)
        # Red, Purple (were there), then Blue, Green (landed on top)
        assert stack.camels == (
            CamelColor.RED, CamelColor.PURPLE,
            CamelColor.BLUE, CamelColor.GREEN
        )

    def test_large_stack_movement(self):
        """Stack of 5+ camels moves correctly."""
        positions = CamelPositions.create_empty()
        # All 5 racing camels at space 3
        for camel in [CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW,
                      CamelColor.RED, CamelColor.PURPLE]:
            positions = positions.place_camel(camel, 3)

        # Move Blue (bottom) - carries all 5
        positions = positions.move_camel(CamelColor.BLUE, 2)

        # All should be at space 5
        stack = positions.get_stack(5)
        assert len(stack) == 5

    def test_stack_ranking(self):
        """Higher in stack = ahead in ranking for same space."""
        positions = CamelPositions.create_empty()
        # Blue at bottom, Green on top at space 5
        positions = positions.place_camel(CamelColor.BLUE, 5)
        positions = positions.place_camel(CamelColor.GREEN, 5)
        # Red alone at space 3
        positions = positions.place_camel(CamelColor.RED, 3)

        ranking = positions.get_ranking()

        # Green (top of stack at 5) > Blue (bottom at 5) > Red (at 3)
        assert ranking[0] == CamelColor.GREEN
        assert ranking[1] == CamelColor.BLUE
        assert ranking[2] == CamelColor.RED


class TestCrazyCamelMovement:
    """Tests for crazy camel movement."""

    def test_crazy_camel_moves_backward(self):
        """Crazy camels move counter-clockwise (backward/negative)."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.WHITE, 10)

        # Move backward 2 spaces
        positions = positions.move_camel(CamelColor.WHITE, -2)

        assert positions.get_camel_space(CamelColor.WHITE) == 8

    def test_crazy_camel_carries_racing_camels_backward(self):
        """Crazy camel moving backward carries any racing camels on top."""
        positions = CamelPositions.create_empty()
        # White at space 10, Blue on top of White
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)

        # White moves backward 3 spaces
        positions = positions.move_camel(CamelColor.WHITE, -3)

        # Both should be at space 7
        assert positions.get_camel_space(CamelColor.WHITE) == 7
        assert positions.get_camel_space(CamelColor.BLUE) == 7

    def test_ranking_ignores_crazy_camels(self):
        """Crazy camels are not included in race ranking."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.WHITE, 15)  # Crazy far ahead
        positions = positions.place_camel(CamelColor.BLUE, 10)
        positions = positions.place_camel(CamelColor.GREEN, 5)

        ranking = positions.get_ranking()

        assert CamelColor.WHITE not in ranking
        assert ranking[0] == CamelColor.BLUE
        assert ranking[1] == CamelColor.GREEN

    def test_crazy_camel_lands_on_racing_camel(self):
        """Crazy camel landing on racing camel goes on top."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 8)
        positions = positions.place_camel(CamelColor.WHITE, 10)

        # White moves backward to space 8
        positions = positions.move_camel(CamelColor.WHITE, -2)

        stack = positions.get_stack(8)
        assert stack.bottom() == CamelColor.BLUE
        assert stack.top() == CamelColor.WHITE

    def test_crazy_camel_at_space_1_boundary(self):
        """Crazy camel cannot go below space 1."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.WHITE, 2)

        # Try to move backward 3 spaces (would be -1)
        positions = positions.move_camel(CamelColor.WHITE, -3)

        # Should stop at space 1 (or handle according to game rules)
        # Current implementation floors at 1
        assert positions.get_camel_space(CamelColor.WHITE) >= 1

    def test_racing_camel_on_crazy_carried_backward(self):
        """Racing camel sitting on crazy camel gets carried backward."""
        positions = CamelPositions.create_empty()
        # Stack: White (bottom), Blue (middle), Green (top) at space 10
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)
        positions = positions.place_camel(CamelColor.GREEN, 10)

        # White moves backward
        positions = positions.move_camel(CamelColor.WHITE, -2)

        # All three at space 8
        assert positions.get_camel_space(CamelColor.WHITE) == 8
        assert positions.get_camel_space(CamelColor.BLUE) == 8
        assert positions.get_camel_space(CamelColor.GREEN) == 8


class TestBoardMovement:
    """Tests for movement through Board class (includes spectator tiles)."""

    def test_board_move_returns_tile_owner(self):
        """Board.move_camel returns spectator tile owner when triggered."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Move blue to space 5
        new_board, tile_owner = board.move_camel(CamelColor.BLUE, 2)

        assert tile_owner == 0

    def test_board_move_no_tile_returns_none(self):
        """Board.move_camel returns None when no tile triggered."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        new_board, tile_owner = board.move_camel(CamelColor.BLUE, 2)

        assert tile_owner is None

    def test_board_game_over_detection(self):
        """Board detects when game is over (camel finished)."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 15)
        board = Board(camel_positions=positions, spectator_tiles={})

        assert not board.is_game_over()

        # Move past finish line
        new_board, _ = board.move_camel(CamelColor.BLUE, 3)
        assert new_board.is_game_over()
