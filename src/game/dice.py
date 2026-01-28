"""Dice and pyramid mechanics for Camel Up."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, List, FrozenSet
import random


class DieColor(Enum):
    """Colors for racing dice (matches racing camels)."""
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    PURPLE = "purple"
    GREY = "grey"  # For crazy camels


# Racing die faces: 1, 1, 2, 2, 3, 3 (6 faces, uniform distribution)
RACING_DIE_FACES: Tuple[int, ...] = (1, 1, 2, 2, 3, 3)

# Grey die faces: determines which crazy camel moves and how far
# White numbers (1, 2, 3) move white camel, black numbers move black camel
# Represented as (camel_color, distance)
GREY_DIE_FACES: Tuple[Tuple[str, int], ...] = (
    ("white", 1), ("white", 2), ("white", 3),
    ("black", 1), ("black", 2), ("black", 3),
)


@dataclass(frozen=True)
class DieRoll:
    """Result of rolling a die."""
    color: DieColor
    value: int
    # For grey die, which crazy camel to move
    crazy_camel: str | None = None


def roll_racing_die(color: DieColor, rng: random.Random | None = None) -> DieRoll:
    """Roll a racing die and return the result."""
    if rng is None:
        rng = random.Random()
    value = rng.choice(RACING_DIE_FACES)
    return DieRoll(color=color, value=value)


def roll_grey_die(rng: random.Random | None = None) -> DieRoll:
    """Roll the grey die and return which crazy camel moves and how far."""
    if rng is None:
        rng = random.Random()
    crazy_camel, value = rng.choice(GREY_DIE_FACES)
    return DieRoll(color=DieColor.GREY, value=value, crazy_camel=crazy_camel)


@dataclass(frozen=True)
class Pyramid:
    """Tracks which dice are still in the pyramid (not yet revealed this leg)."""
    # Dice still in pyramid (racing dice only, grey is always available)
    remaining: FrozenSet[DieColor] = field(
        default_factory=lambda: frozenset({
            DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW,
            DieColor.RED, DieColor.PURPLE
        })
    )
    # Whether grey die has been rolled this leg
    grey_rolled: bool = False

    def is_leg_complete(self) -> bool:
        """A leg ends when 5 of 6 dice have been revealed (1 remains)."""
        remaining_count = len(self.remaining) + (0 if self.grey_rolled else 1)
        return remaining_count == 1

    def can_roll(self, color: DieColor) -> bool:
        """Check if a specific die can still be rolled."""
        if color == DieColor.GREY:
            return not self.grey_rolled
        return color in self.remaining

    def get_available_racing_dice(self) -> FrozenSet[DieColor]:
        """Get the set of racing dice still in the pyramid."""
        return self.remaining

    def roll_from_pyramid(self, rng: random.Random | None = None) -> Tuple["Pyramid", DieRoll]:
        """
        Randomly select and roll a die from the pyramid.
        Returns new pyramid state and the roll result.
        """
        if rng is None:
            rng = random.Random()

        # Build list of available dice
        available: List[DieColor] = list(self.remaining)
        if not self.grey_rolled:
            available.append(DieColor.GREY)

        if not available:
            raise ValueError("No dice remaining in pyramid")

        # Select random die
        selected = rng.choice(available)

        # Roll the selected die
        if selected == DieColor.GREY:
            roll = roll_grey_die(rng)
            new_pyramid = Pyramid(remaining=self.remaining, grey_rolled=True)
        else:
            roll = roll_racing_die(selected, rng)
            new_pyramid = Pyramid(
                remaining=self.remaining - {selected},
                grey_rolled=self.grey_rolled
            )

        return new_pyramid, roll

    def reset(self) -> "Pyramid":
        """Reset pyramid for a new leg."""
        return Pyramid()


def get_racing_die_probabilities() -> dict[int, float]:
    """Return probability distribution for racing die."""
    # Each value (1, 2, 3) appears twice on 6 faces = 1/3 each
    return {1: 1/3, 2: 1/3, 3: 1/3}


def get_racing_die_expected_value() -> float:
    """Return expected value of a racing die roll."""
    probs = get_racing_die_probabilities()
    return sum(val * prob for val, prob in probs.items())  # = 2.0
