"""Tests for camel and stacking mechanics."""

import pytest
from src.game.camel import (
    CamelColor, CamelStack, CamelPositions,
    RACING_CAMELS, CRAZY_CAMELS, create_initial_positions
)


class TestCamelColor:
    """Tests for CamelColor enum."""

    def test_racing_camels(self):
        """There are 5 racing camels."""
        assert len(RACING_CAMELS) == 5
        assert CamelColor.BLUE in RACING_CAMELS
        assert CamelColor.GREEN in RACING_CAMELS
        assert CamelColor.YELLOW in RACING_CAMELS
        assert CamelColor.RED in RACING_CAMELS
        assert CamelColor.PURPLE in RACING_CAMELS

    def test_crazy_camels(self):
        """There are 2 crazy camels."""
        assert len(CRAZY_CAMELS) == 2
        assert CamelColor.WHITE in CRAZY_CAMELS
        assert CamelColor.BLACK in CRAZY_CAMELS

    def test_is_racing_camel(self):
        """is_racing_camel correctly identifies racing camels."""
        assert CamelColor.BLUE.is_racing_camel()
        assert not CamelColor.WHITE.is_racing_camel()

    def test_is_crazy_camel(self):
        """is_crazy_camel correctly identifies crazy camels."""
        assert CamelColor.BLACK.is_crazy_camel()
        assert not CamelColor.RED.is_crazy_camel()


class TestCamelStack:
    """Tests for camel stack mechanics."""

    def test_empty_stack(self):
        """Empty stack has no camels."""
        stack = CamelStack.empty()
        assert len(stack) == 0
        assert not stack
        assert stack.top() is None
        assert stack.bottom() is None

    def test_from_camels(self):
        """Create stack from bottom to top."""
        stack = CamelStack.from_camels(CamelColor.BLUE, CamelColor.GREEN)
        assert len(stack) == 2
        assert stack.bottom() == CamelColor.BLUE
        assert stack.top() == CamelColor.GREEN

    def test_position_of(self):
        """Get position of camel in stack."""
        stack = CamelStack.from_camels(
            CamelColor.BLUE, CamelColor.GREEN, CamelColor.RED
        )
        assert stack.position_of(CamelColor.BLUE) == 0
        assert stack.position_of(CamelColor.GREEN) == 1
        assert stack.position_of(CamelColor.RED) == 2
        assert stack.position_of(CamelColor.YELLOW) is None

    def test_get_camels_above(self):
        """Get camels above a given camel (including itself)."""
        stack = CamelStack.from_camels(
            CamelColor.BLUE, CamelColor.GREEN, CamelColor.RED
        )
        above = stack.get_camels_above(CamelColor.GREEN)
        assert above == (CamelColor.GREEN, CamelColor.RED)

    def test_get_camels_below(self):
        """Get camels below a given camel (not including itself)."""
        stack = CamelStack.from_camels(
            CamelColor.BLUE, CamelColor.GREEN, CamelColor.RED
        )
        below = stack.get_camels_below(CamelColor.RED)
        assert below == (CamelColor.BLUE, CamelColor.GREEN)

    def test_remove_camels_from(self):
        """Remove camel and all above from stack."""
        stack = CamelStack.from_camels(
            CamelColor.BLUE, CamelColor.GREEN, CamelColor.RED
        )
        remaining, removed = stack.remove_camels_from(CamelColor.GREEN)

        assert remaining.camels == (CamelColor.BLUE,)
        assert removed.camels == (CamelColor.GREEN, CamelColor.RED)

    def test_add_on_top(self):
        """Add another stack on top."""
        stack1 = CamelStack.from_camels(CamelColor.BLUE)
        stack2 = CamelStack.from_camels(CamelColor.GREEN, CamelColor.RED)

        combined = stack1.add_on_top(stack2)
        assert combined.camels == (CamelColor.BLUE, CamelColor.GREEN, CamelColor.RED)

    def test_add_underneath(self):
        """Add another stack underneath."""
        stack1 = CamelStack.from_camels(CamelColor.BLUE)
        stack2 = CamelStack.from_camels(CamelColor.GREEN, CamelColor.RED)

        combined = stack1.add_underneath(stack2)
        assert combined.camels == (CamelColor.GREEN, CamelColor.RED, CamelColor.BLUE)

    def test_get_racing_camels(self):
        """Filter to only racing camels."""
        stack = CamelStack.from_camels(
            CamelColor.WHITE, CamelColor.BLUE, CamelColor.BLACK, CamelColor.GREEN
        )
        racing = stack.get_racing_camels()
        assert racing == (CamelColor.BLUE, CamelColor.GREEN)

    def test_get_top_racing_camel(self):
        """Get topmost racing camel in mixed stack."""
        stack = CamelStack.from_camels(
            CamelColor.BLUE, CamelColor.WHITE, CamelColor.GREEN, CamelColor.BLACK
        )
        top_racing = stack.get_top_racing_camel()
        assert top_racing == CamelColor.GREEN


class TestCamelPositions:
    """Tests for camel position tracking."""

    def test_create_empty(self):
        """Create empty positions."""
        positions = CamelPositions.create_empty()
        assert all(not positions.get_stack(i) for i in range(20))

    def test_move_camel_simple(self):
        """Move a single camel forward."""
        # Place blue at space 3
        positions = CamelPositions.create_empty()
        positions = positions.move_camel(CamelColor.BLUE, 3)

        assert positions.get_camel_space(CamelColor.BLUE) == 3
        assert CamelColor.BLUE in positions.get_stack(3)

    def test_move_camel_carries_stack(self):
        """Moving camel carries all camels on top."""
        # Create stack: Blue (bottom), Green (top) at space 3
        positions = CamelPositions.create_empty()
        positions = positions.move_camel(CamelColor.BLUE, 3)
        positions = positions.move_camel(CamelColor.GREEN, 3)

        # Green is now on top of Blue
        stack = positions.get_stack(3)
        assert stack.bottom() == CamelColor.BLUE
        assert stack.top() == CamelColor.GREEN

        # Move Blue forward 2 spaces - should carry Green
        positions = positions.move_camel(CamelColor.BLUE, 2)

        # Both should now be at space 5
        assert positions.get_camel_space(CamelColor.BLUE) == 5
        assert positions.get_camel_space(CamelColor.GREEN) == 5

        # Blue should still be on bottom
        stack = positions.get_stack(5)
        assert stack.bottom() == CamelColor.BLUE
        assert stack.top() == CamelColor.GREEN

    def test_move_lands_on_top(self):
        """Moving camel lands on top of existing stack."""
        # Place Blue at space 3, Red at space 5
        positions = CamelPositions.create_empty()
        positions = positions.move_camel(CamelColor.RED, 5)
        positions = positions.move_camel(CamelColor.BLUE, 3)

        # Move Blue 2 spaces to land on Red
        positions = positions.move_camel(CamelColor.BLUE, 2)

        stack = positions.get_stack(5)
        assert stack.bottom() == CamelColor.RED
        assert stack.top() == CamelColor.BLUE

    def test_move_underneath(self):
        """Moving with place_underneath puts camel below existing."""
        # Place Blue at space 5
        positions = CamelPositions.create_empty()
        positions = positions.move_camel(CamelColor.BLUE, 5)

        # Place Red at space 3, then move with place_underneath
        positions = positions.move_camel(CamelColor.RED, 3)
        positions = positions.move_camel(CamelColor.RED, 2, place_underneath=True)

        stack = positions.get_stack(5)
        assert stack.bottom() == CamelColor.RED  # Red went underneath
        assert stack.top() == CamelColor.BLUE

    def test_get_ranking(self):
        """Ranking orders camels by position and stack height."""
        positions = CamelPositions.create_empty()
        # Blue at space 5, Green on top of Blue, Red at space 3
        positions = positions.move_camel(CamelColor.BLUE, 5)
        positions = positions.move_camel(CamelColor.GREEN, 5)
        positions = positions.move_camel(CamelColor.RED, 3)

        ranking = positions.get_ranking()

        # Green (top at 5) > Blue (bottom at 5) > Red (at 3)
        assert ranking[0] == CamelColor.GREEN
        assert ranking[1] == CamelColor.BLUE
        assert ranking[2] == CamelColor.RED

    def test_ranking_ignores_crazy_camels(self):
        """Ranking only includes racing camels."""
        positions = CamelPositions.create_empty()
        positions = positions.move_camel(CamelColor.WHITE, 10)  # Crazy camel ahead
        positions = positions.move_camel(CamelColor.BLUE, 5)

        ranking = positions.get_ranking()
        assert CamelColor.WHITE not in ranking
        assert CamelColor.BLUE in ranking


class TestCrazyCamelRules:
    """Tests for crazy camel priority and stack rules."""

    def test_has_racing_camels_on_back(self):
        """Check if crazy camel has racing camels on its back."""
        positions = CamelPositions.create_empty()
        # Stack: White (bottom), Blue (top) at space 10
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)

        assert positions.has_racing_camels_on_back(CamelColor.WHITE) is True

        # Black alone at space 5
        positions = positions.place_camel(CamelColor.BLACK, 5)
        assert positions.has_racing_camels_on_back(CamelColor.BLACK) is False

    def test_crazy_camel_priority_rule(self):
        """If only one crazy camel has racers on back, move that one."""
        positions = CamelPositions.create_empty()
        # White has Blue on its back
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)
        # Black is alone
        positions = positions.place_camel(CamelColor.BLACK, 5)

        # Grey die shows Black, but White has racers, so White should move
        camel_to_move = positions.get_crazy_camel_to_move(CamelColor.BLACK)
        assert camel_to_move == CamelColor.WHITE

        # Grey die shows White, White has racers, so White should move
        camel_to_move = positions.get_crazy_camel_to_move(CamelColor.WHITE)
        assert camel_to_move == CamelColor.WHITE

    def test_crazy_camel_priority_both_have_racers(self):
        """If both crazy camels have racers, use die color."""
        positions = CamelPositions.create_empty()
        # White has Blue on its back
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)
        # Black has Green on its back
        positions = positions.place_camel(CamelColor.BLACK, 5)
        positions = positions.place_camel(CamelColor.GREEN, 5)

        # Both have racers, so use die color
        assert positions.get_crazy_camel_to_move(CamelColor.WHITE) == CamelColor.WHITE
        assert positions.get_crazy_camel_to_move(CamelColor.BLACK) == CamelColor.BLACK

    def test_crazy_camel_stack_rule(self):
        """If crazy camels stacked directly (no racers between), move top one."""
        positions = CamelPositions.create_empty()
        # Stack: White (bottom), Black (top) at space 10 - no racers between
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLACK, 10)

        # Grey die shows White, but Black is on top, so Black moves
        camel_to_move = positions.get_crazy_camel_to_move(CamelColor.WHITE)
        assert camel_to_move == CamelColor.BLACK

        # Grey die shows Black, Black is on top, so Black moves
        camel_to_move = positions.get_crazy_camel_to_move(CamelColor.BLACK)
        assert camel_to_move == CamelColor.BLACK

    def test_crazy_camel_stack_with_racer_between(self):
        """If racing camel between crazy camels, use die color."""
        positions = CamelPositions.create_empty()
        # Stack: White (bottom), Blue (middle), Black (top) at space 10
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLUE, 10)
        positions = positions.place_camel(CamelColor.BLACK, 10)

        # Both have racers on back technically, but Blue is between them
        # Since both have racers (sort of), and there's a racer between, use die
        # Actually White has Blue on back, Black has nothing on back
        # So White should move per priority rule
        camel_to_move = positions.get_crazy_camel_to_move(CamelColor.BLACK)
        assert camel_to_move == CamelColor.WHITE

    def test_crazy_camel_neither_rule_applies(self):
        """If neither rule applies, use die color."""
        positions = CamelPositions.create_empty()
        # Both camels alone on different spaces
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLACK, 5)

        # Neither has racers, not stacked, use die color
        assert positions.get_crazy_camel_to_move(CamelColor.WHITE) == CamelColor.WHITE
        assert positions.get_crazy_camel_to_move(CamelColor.BLACK) == CamelColor.BLACK


class TestInitialPositions:
    """Tests for initial game setup."""

    def test_create_initial_positions(self):
        """Create positions from dice rolls."""
        dice_rolls = [
            (CamelColor.BLUE, 1),
            (CamelColor.GREEN, 2),
            (CamelColor.YELLOW, 1),
            (CamelColor.RED, 3),
            (CamelColor.PURPLE, 2),
        ]

        positions = create_initial_positions(dice_rolls)

        # Blue and Yellow rolled 1, should be at space 1
        assert positions.get_camel_space(CamelColor.BLUE) == 1
        assert positions.get_camel_space(CamelColor.YELLOW) == 1

        # Green and Purple rolled 2, should be at space 2
        assert positions.get_camel_space(CamelColor.GREEN) == 2
        assert positions.get_camel_space(CamelColor.PURPLE) == 2

        # Red rolled 3, should be at space 3
        assert positions.get_camel_space(CamelColor.RED) == 3
