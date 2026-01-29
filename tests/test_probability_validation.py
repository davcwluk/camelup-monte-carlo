"""Monte Carlo validation tests for probability calculator.

Validates that calculator.py predictions match actual outcomes by independently
simulating thousands of random legs using Board.move_camel() directly (NOT
reusing calculator enumeration code). This is a critical pre-Phase 4 test --
if the calculator is wrong, all EV calculations are invalid.
"""

import random
from collections import defaultdict
from typing import Dict, List, Tuple

import pytest

from src.game.board import Board
from src.game.camel import (
    CamelColor,
    CamelPositions,
    RACING_CAMELS,
    CRAZY_CAMELS,
)
from src.game.dice import DieColor
from src.probability.calculator import (
    calculate_all_probabilities,
    enumerate_grey_die_outcomes,
)


# ---------------------------------------------------------------------------
# Helper: independent Monte Carlo leg simulation
# ---------------------------------------------------------------------------

def simulate_random_leg(
    board: Board,
    remaining_dice: List[DieColor],
    grey_die_available: bool,
    rng: random.Random,
) -> Tuple[CamelColor, ...]:
    """Simulate a single random leg and return the final ranking.

    This intentionally does NOT reuse any calculator.py enumeration logic.
    It draws dice in a random order, rolls random values, and applies
    Board.move_camel() directly.

    Returns:
        Tuple of CamelColor in ranking order (1st to last, racing camels only).
    """
    current_board = board

    # Build a pool of dice to draw from: racing dice + optionally grey
    pool: List[str] = ["racing"] * len(remaining_dice)
    if grey_die_available:
        pool.append("grey")
    rng.shuffle(pool)

    racing_remaining = list(remaining_dice)
    rng.shuffle(racing_remaining)
    racing_idx = 0

    # A leg ends when 1 die remains in the pyramid. Draw len(remaining_dice)
    # dice -- when grey is included, that leaves 1 behind; when grey is
    # excluded, we roll all racing dice (the untracked grey is left behind).
    dice_to_draw = len(remaining_dice)

    for token in pool[:dice_to_draw]:
        if token == "grey":
            # Pick one of the 6 grey die outcomes uniformly
            grey_outcomes = enumerate_grey_die_outcomes()
            grey_camel_shown, value = rng.choice(grey_outcomes)
            # Apply crazy camel priority rules
            actual_camel = current_board.camel_positions.get_crazy_camel_to_move(
                grey_camel_shown
            )
            current_board, _ = current_board.move_camel(actual_camel, -value)
        else:
            # Racing die
            die_color = racing_remaining[racing_idx]
            racing_idx += 1
            value = rng.choice([1, 2, 3])
            camel = CamelColor[die_color.name]
            current_board, _ = current_board.move_camel(camel, value)

        if current_board.is_game_over():
            break

    ranking = tuple(current_board.get_ranking())
    return ranking


def run_monte_carlo(
    board: Board,
    remaining_dice: List[DieColor],
    grey_die_available: bool,
    n_simulations: int,
    seed: int = 42,
) -> Dict[CamelColor, List[int]]:
    """Run N random leg simulations and count position frequencies.

    Returns:
        Dict mapping camel -> list of counts per position (index 0 = 1st place).
    """
    rng = random.Random(seed)
    counts: Dict[CamelColor, List[int]] = {
        camel: [0] * 5 for camel in RACING_CAMELS
    }

    for _ in range(n_simulations):
        ranking = simulate_random_leg(
            board, remaining_dice, grey_die_available, rng
        )
        for pos, camel in enumerate(ranking):
            if camel in counts and pos < 5:
                counts[camel][pos] += 1

    return counts


# ---------------------------------------------------------------------------
# Board factory helpers
# ---------------------------------------------------------------------------

def _all_racing_dice() -> List[DieColor]:
    return [DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW,
            DieColor.RED, DieColor.PURPLE]


def _make_spread_board() -> Board:
    """Camels spread across spaces 1-5 (no stacking)."""
    positions = CamelPositions.create_empty()
    positions = positions.place_camel(CamelColor.BLUE, 1)
    positions = positions.place_camel(CamelColor.GREEN, 2)
    positions = positions.place_camel(CamelColor.YELLOW, 3)
    positions = positions.place_camel(CamelColor.RED, 4)
    positions = positions.place_camel(CamelColor.PURPLE, 5)
    return Board(camel_positions=positions, spectator_tiles={})


def _make_stacked_board() -> Board:
    """All 5 camels stacked on a single space (space 3)."""
    positions = CamelPositions.create_empty()
    for camel in [CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW,
                  CamelColor.RED, CamelColor.PURPLE]:
        positions = positions.place_camel(camel, 3)
    return Board(camel_positions=positions, spectator_tiles={})


def _make_mid_leg_board() -> Board:
    """Mid-leg scenario: some camels ahead, some behind, partial stacking."""
    positions = CamelPositions.create_empty()
    positions = positions.place_camel(CamelColor.BLUE, 6)
    positions = positions.place_camel(CamelColor.GREEN, 6)   # stacked on Blue
    positions = positions.place_camel(CamelColor.YELLOW, 4)
    positions = positions.place_camel(CamelColor.RED, 4)     # stacked on Yellow
    positions = positions.place_camel(CamelColor.PURPLE, 2)
    return Board(camel_positions=positions, spectator_tiles={})


def _make_near_finish_board() -> Board:
    """Camels near the finish line -- high probability of game ending."""
    positions = CamelPositions.create_empty()
    positions = positions.place_camel(CamelColor.BLUE, 15)
    positions = positions.place_camel(CamelColor.GREEN, 14)
    positions = positions.place_camel(CamelColor.YELLOW, 13)
    positions = positions.place_camel(CamelColor.RED, 12)
    positions = positions.place_camel(CamelColor.PURPLE, 11)
    return Board(camel_positions=positions, spectator_tiles={})


def _make_spread_board_with_crazy() -> Board:
    """Spread board with crazy camels placed on the track."""
    positions = CamelPositions.create_empty()
    positions = positions.place_camel(CamelColor.BLUE, 3)
    positions = positions.place_camel(CamelColor.GREEN, 5)
    positions = positions.place_camel(CamelColor.YELLOW, 7)
    positions = positions.place_camel(CamelColor.RED, 9)
    positions = positions.place_camel(CamelColor.PURPLE, 11)
    positions = positions.place_camel(CamelColor.WHITE, 14)
    positions = positions.place_camel(CamelColor.BLACK, 16)
    return Board(camel_positions=positions, spectator_tiles={})


def _make_stacked_with_crazy_board() -> Board:
    """Stacked racing camels with crazy camels nearby."""
    positions = CamelPositions.create_empty()
    positions = positions.place_camel(CamelColor.BLUE, 5)
    positions = positions.place_camel(CamelColor.GREEN, 5)
    positions = positions.place_camel(CamelColor.YELLOW, 5)
    positions = positions.place_camel(CamelColor.RED, 8)
    positions = positions.place_camel(CamelColor.PURPLE, 8)
    positions = positions.place_camel(CamelColor.WHITE, 6)
    positions = positions.place_camel(CamelColor.BLACK, 9)
    return Board(camel_positions=positions, spectator_tiles={})


# ---------------------------------------------------------------------------
# Comparison helper
# ---------------------------------------------------------------------------

TOLERANCE = 0.03  # ~6 standard errors at N=10,000 for p near 0.5

def assert_probabilities_match(
    predicted: Dict[CamelColor, Tuple[float, ...]],
    empirical_counts: Dict[CamelColor, List[int]],
    n_simulations: int,
    tolerance: float = TOLERANCE,
    positions_to_check: int = 1,
) -> None:
    """Assert predicted probabilities match empirical frequencies within tolerance.

    Args:
        predicted: camel -> tuple of probabilities per position (from calculator).
        empirical_counts: camel -> list of counts per position (from MC sim).
        n_simulations: total number of simulations run.
        tolerance: maximum allowed absolute difference.
        positions_to_check: how many positions to validate (1 = first only, 5 = all).
    """
    for camel in RACING_CAMELS:
        pred_probs = predicted[camel]
        emp_counts = empirical_counts[camel]
        for pos in range(positions_to_check):
            pred_p = pred_probs[pos]
            emp_p = emp_counts[pos] / n_simulations
            diff = abs(pred_p - emp_p)
            assert diff < tolerance, (
                f"{camel.value} position {pos + 1}: "
                f"predicted={pred_p:.4f}, empirical={emp_p:.4f}, "
                f"diff={diff:.4f} > tolerance={tolerance}"
            )


# ---------------------------------------------------------------------------
# Fast-mode tests (no grey die) -- 10,000 simulations each
# ---------------------------------------------------------------------------

N_FAST = 10_000


class TestMonteCarloValidation:
    """Validate calculator predictions against independent Monte Carlo simulation
    (fast_mode -- no grey die)."""

    def test_spread_board_fast_mode(self):
        board = _make_spread_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)
        counts = run_monte_carlo(board, dice, grey_die_available=False,
                                 n_simulations=N_FAST, seed=101)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FAST
        )

    def test_stacked_board_fast_mode(self):
        board = _make_stacked_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)
        counts = run_monte_carlo(board, dice, grey_die_available=False,
                                 n_simulations=N_FAST, seed=202)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FAST
        )

    def test_mid_leg_fast_mode(self):
        board = _make_mid_leg_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)
        counts = run_monte_carlo(board, dice, grey_die_available=False,
                                 n_simulations=N_FAST, seed=303)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FAST
        )

    def test_near_finish_fast_mode(self):
        board = _make_near_finish_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)
        counts = run_monte_carlo(board, dice, grey_die_available=False,
                                 n_simulations=N_FAST, seed=404)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FAST
        )

    def test_all_positions_validated(self):
        """Check all 5 ranking positions, not just 1st place."""
        board = _make_spread_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)
        counts = run_monte_carlo(board, dice, grey_die_available=False,
                                 n_simulations=N_FAST, seed=505)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FAST,
            positions_to_check=5,
        )

    def test_probabilities_sum_validation(self):
        """Verify that predicted probabilities sum to 1.0 for each position."""
        board = _make_mid_leg_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=False)

        # For each position, sum across all camels should be ~1.0
        for pos in range(5):
            total = sum(
                probs.ranking.probabilities[camel][pos]
                for camel in RACING_CAMELS
            )
            assert abs(total - 1.0) < 0.0001, (
                f"Position {pos + 1}: probabilities sum to {total}, expected 1.0"
            )

        # For each camel, sum across all positions should be ~1.0
        for camel in RACING_CAMELS:
            total = sum(probs.ranking.probabilities[camel])
            assert abs(total - 1.0) < 0.0001, (
                f"{camel.value}: position probabilities sum to {total}, expected 1.0"
            )


# ---------------------------------------------------------------------------
# Full-mode tests (with grey die) -- 5,000 simulations, marked slow
# ---------------------------------------------------------------------------

N_FULL = 5_000
TOLERANCE_FULL = 0.04  # Slightly wider for fewer simulations


class TestLegStopsAfterFiveDice:
    """Verify the calculator stops after 5 dice (1 remains in pyramid).

    This is the critical correctness test: a leg ends when 5 of 6 dice are
    revealed. If the calculator simulates all 6 dice, rankings are wrong
    because an extra camel move occurs after the leg should have ended.
    """

    def test_sixth_die_not_simulated(self):
        """Only Blue's die + grey remain. One is drawn, one stays.

        Setup: Blue at 14, Green at 15. Other racers far behind. Crazy
        camels at space 10 (won't interfere).

        Correct (1 die drawn from 2 remaining):
          - Blue drawn (50%): Blue moves to 15-17, overtakes Green -> Blue 1st
          - Grey drawn (50%): crazy camel moves, Blue stays at 14 -> Green 1st
          P(Blue 1st) = 0.5

        Buggy (both dice drawn):
          Blue always moves -> P(Blue 1st) = 1.0
        """
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 14)
        positions = positions.place_camel(CamelColor.GREEN, 15)
        positions = positions.place_camel(CamelColor.YELLOW, 1)
        positions = positions.place_camel(CamelColor.RED, 1)
        positions = positions.place_camel(CamelColor.PURPLE, 1)
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLACK, 10)
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_all_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE],
            grey_die_available=True,
        )

        p_blue_first = probs.ranking.probabilities[CamelColor.BLUE][0]
        assert abs(p_blue_first - 0.5) < 0.01, (
            f"P(Blue 1st) = {p_blue_first:.4f}, expected 0.5. "
            f"If ~1.0, the calculator is simulating the 6th die (bug)."
        )

    def test_sixth_die_not_simulated_mc_agrees(self):
        """Monte Carlo validator also stops after 5 dice."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 14)
        positions = positions.place_camel(CamelColor.GREEN, 15)
        positions = positions.place_camel(CamelColor.YELLOW, 1)
        positions = positions.place_camel(CamelColor.RED, 1)
        positions = positions.place_camel(CamelColor.PURPLE, 1)
        positions = positions.place_camel(CamelColor.WHITE, 10)
        positions = positions.place_camel(CamelColor.BLACK, 10)
        board = Board(camel_positions=positions, spectator_tiles={})

        counts = run_monte_carlo(
            board, [DieColor.BLUE], grey_die_available=True,
            n_simulations=10_000, seed=888,
        )

        p_blue_first = counts[CamelColor.BLUE][0] / 10_000
        assert abs(p_blue_first - 0.5) < 0.03, (
            f"MC P(Blue 1st) = {p_blue_first:.4f}, expected ~0.5. "
            f"If ~1.0, the MC validator is simulating the 6th die (bug)."
        )


@pytest.mark.slow
class TestMonteCarloValidationWithGreyDie:
    """Validate calculator predictions with grey die (full mode).

    These tests are slower because:
    - The calculator enumerates ~1M outcomes instead of ~29K.
    - We still run 5,000 MC simulations for comparison.
    """

    def test_spread_board_full_mode(self):
        board = _make_spread_board_with_crazy()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=True)
        counts = run_monte_carlo(board, dice, grey_die_available=True,
                                 n_simulations=N_FULL, seed=601)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FULL,
            tolerance=TOLERANCE_FULL,
        )

    def test_stacked_with_crazy_camels(self):
        board = _make_stacked_with_crazy_board()
        dice = _all_racing_dice()

        probs = calculate_all_probabilities(board, dice, grey_die_available=True)
        counts = run_monte_carlo(board, dice, grey_die_available=True,
                                 n_simulations=N_FULL, seed=701)

        assert_probabilities_match(
            probs.ranking.probabilities, counts, N_FULL,
            tolerance=TOLERANCE_FULL,
        )
