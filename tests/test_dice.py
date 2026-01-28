"""Tests for dice and pyramid mechanics."""

import pytest
import random
from src.game.dice import (
    DieColor, DieRoll, Pyramid,
    roll_racing_die, roll_grey_die,
    RACING_DIE_FACES, GREY_DIE_FACES,
    get_racing_die_probabilities, get_racing_die_expected_value
)


class TestRacingDie:
    """Tests for racing die mechanics."""

    def test_racing_die_faces(self):
        """Racing die has 6 faces: 1, 1, 2, 2, 3, 3."""
        assert RACING_DIE_FACES == (1, 1, 2, 2, 3, 3)
        assert len(RACING_DIE_FACES) == 6

    def test_roll_racing_die_returns_valid_value(self):
        """Rolling a racing die returns a value from 1-3."""
        rng = random.Random(42)
        for _ in range(100):
            roll = roll_racing_die(DieColor.BLUE, rng)
            assert roll.value in [1, 2, 3]
            assert roll.color == DieColor.BLUE
            assert roll.crazy_camel is None

    def test_racing_die_distribution(self):
        """Racing die has uniform probability distribution (1/3 each)."""
        rng = random.Random(42)
        counts = {1: 0, 2: 0, 3: 0}

        for _ in range(10000):
            roll = roll_racing_die(DieColor.GREEN, rng)
            counts[roll.value] += 1

        # Expected: 33.3% for each value
        assert 0.30 < counts[1] / 10000 < 0.37  # ~33%
        assert 0.30 < counts[2] / 10000 < 0.37  # ~33%
        assert 0.30 < counts[3] / 10000 < 0.37  # ~33%

    def test_racing_die_probabilities(self):
        """Probability helper returns correct values (1/3 each)."""
        probs = get_racing_die_probabilities()
        assert probs[1] == pytest.approx(1/3)
        assert probs[2] == pytest.approx(1/3)
        assert probs[3] == pytest.approx(1/3)

    def test_racing_die_expected_value(self):
        """Expected value is 2.0."""
        ev = get_racing_die_expected_value()
        assert ev == pytest.approx(2.0)


class TestGreyDie:
    """Tests for grey die mechanics."""

    def test_grey_die_faces(self):
        """Grey die has 6 faces for two crazy camels."""
        assert len(GREY_DIE_FACES) == 6
        white_faces = [f for f in GREY_DIE_FACES if f[0] == "white"]
        black_faces = [f for f in GREY_DIE_FACES if f[0] == "black"]
        assert len(white_faces) == 3
        assert len(black_faces) == 3

    def test_roll_grey_die_returns_valid_result(self):
        """Rolling grey die returns camel color and movement."""
        rng = random.Random(42)
        for _ in range(100):
            roll = roll_grey_die(rng)
            assert roll.value in [1, 2, 3]
            assert roll.color == DieColor.GREY
            assert roll.crazy_camel in ["white", "black"]


class TestPyramid:
    """Tests for pyramid mechanics."""

    def test_initial_pyramid_has_all_dice(self):
        """New pyramid has all 5 racing dice."""
        pyramid = Pyramid()
        assert len(pyramid.remaining) == 5
        assert DieColor.BLUE in pyramid.remaining
        assert DieColor.GREEN in pyramid.remaining
        assert DieColor.YELLOW in pyramid.remaining
        assert DieColor.RED in pyramid.remaining
        assert DieColor.PURPLE in pyramid.remaining
        assert not pyramid.grey_rolled

    def test_roll_from_pyramid_removes_die(self):
        """Rolling from pyramid removes the die."""
        rng = random.Random(42)
        pyramid = Pyramid()

        new_pyramid, roll = pyramid.roll_from_pyramid(rng)

        if roll.color == DieColor.GREY:
            assert new_pyramid.grey_rolled
            assert len(new_pyramid.remaining) == 5
        else:
            assert roll.color not in new_pyramid.remaining
            assert len(new_pyramid.remaining) == 4

    def test_leg_complete_when_one_die_remains(self):
        """Leg is complete when only 1 of 6 dice remains."""
        # Start with full pyramid
        pyramid = Pyramid()
        assert not pyramid.is_leg_complete()

        # Remove 4 racing dice (1 racing + grey remain)
        pyramid = Pyramid(
            remaining=frozenset({DieColor.BLUE}),
            grey_rolled=False
        )
        assert not pyramid.is_leg_complete()  # 2 dice remain

        # Remove grey die too (1 racing remains)
        pyramid = Pyramid(
            remaining=frozenset({DieColor.BLUE}),
            grey_rolled=True
        )
        assert pyramid.is_leg_complete()  # 1 die remains

    def test_can_roll_checks_availability(self):
        """can_roll returns correct availability."""
        pyramid = Pyramid(
            remaining=frozenset({DieColor.BLUE, DieColor.GREEN}),
            grey_rolled=True
        )

        assert pyramid.can_roll(DieColor.BLUE)
        assert pyramid.can_roll(DieColor.GREEN)
        assert not pyramid.can_roll(DieColor.RED)
        assert not pyramid.can_roll(DieColor.GREY)

    def test_reset_pyramid(self):
        """Reset returns a fresh pyramid."""
        pyramid = Pyramid(
            remaining=frozenset({DieColor.BLUE}),
            grey_rolled=True
        )
        reset = pyramid.reset()

        assert len(reset.remaining) == 5
        assert not reset.grey_rolled
