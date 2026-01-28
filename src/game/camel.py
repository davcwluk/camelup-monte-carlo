"""Camel and stacking mechanics for Camel Up."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class CamelColor(Enum):
    """All camel colors in the game."""
    # Racing camels (move clockwise)
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    PURPLE = "purple"
    # Crazy camels (move counter-clockwise)
    WHITE = "white"
    BLACK = "black"

    def is_racing_camel(self) -> bool:
        """Check if this is a racing camel (not crazy)."""
        return self in RACING_CAMELS

    def is_crazy_camel(self) -> bool:
        """Check if this is a crazy camel."""
        return self in CRAZY_CAMELS


# Camel groups
RACING_CAMELS = frozenset({
    CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW,
    CamelColor.RED, CamelColor.PURPLE
})

CRAZY_CAMELS = frozenset({CamelColor.WHITE, CamelColor.BLACK})

ALL_CAMELS = RACING_CAMELS | CRAZY_CAMELS


@dataclass(frozen=True)
class CamelStack:
    """
    Represents a stack of camels on a single space.

    The stack is ordered from bottom to top (index 0 = bottom, last = top).
    A camel higher in the stack is considered "ahead" for ranking purposes.
    """
    camels: Tuple[CamelColor, ...]

    def __len__(self) -> int:
        return len(self.camels)

    def __bool__(self) -> bool:
        return len(self.camels) > 0

    def __contains__(self, camel: CamelColor) -> bool:
        return camel in self.camels

    @classmethod
    def empty(cls) -> "CamelStack":
        """Create an empty stack."""
        return cls(camels=())

    @classmethod
    def from_camels(cls, *camels: CamelColor) -> "CamelStack":
        """Create a stack from bottom to top."""
        return cls(camels=tuple(camels))

    def top(self) -> CamelColor | None:
        """Get the camel on top of the stack."""
        return self.camels[-1] if self.camels else None

    def bottom(self) -> CamelColor | None:
        """Get the camel at the bottom of the stack."""
        return self.camels[0] if self.camels else None

    def position_of(self, camel: CamelColor) -> int | None:
        """Get the position of a camel in the stack (0 = bottom)."""
        try:
            return self.camels.index(camel)
        except ValueError:
            return None

    def get_camels_above(self, camel: CamelColor) -> Tuple[CamelColor, ...]:
        """Get all camels sitting on top of the given camel (including itself)."""
        pos = self.position_of(camel)
        if pos is None:
            return ()
        return self.camels[pos:]

    def get_camels_below(self, camel: CamelColor) -> Tuple[CamelColor, ...]:
        """Get all camels below the given camel (not including itself)."""
        pos = self.position_of(camel)
        if pos is None:
            return ()
        return self.camels[:pos]

    def remove_camels_from(self, camel: CamelColor) -> Tuple["CamelStack", "CamelStack"]:
        """
        Remove a camel and all camels above it from the stack.
        Returns (remaining_stack, removed_stack).
        """
        pos = self.position_of(camel)
        if pos is None:
            return self, CamelStack.empty()

        remaining = CamelStack(camels=self.camels[:pos])
        removed = CamelStack(camels=self.camels[pos:])
        return remaining, removed

    def add_on_top(self, other: "CamelStack") -> "CamelStack":
        """Add another stack on top of this stack."""
        return CamelStack(camels=self.camels + other.camels)

    def add_underneath(self, other: "CamelStack") -> "CamelStack":
        """Add another stack underneath this stack."""
        return CamelStack(camels=other.camels + self.camels)

    def get_racing_camels(self) -> Tuple[CamelColor, ...]:
        """Get only the racing camels in this stack (in order)."""
        return tuple(c for c in self.camels if c.is_racing_camel())

    def get_top_racing_camel(self) -> CamelColor | None:
        """Get the topmost racing camel in this stack."""
        for camel in reversed(self.camels):
            if camel.is_racing_camel():
                return camel
        return None


@dataclass(frozen=True)
class CamelPositions:
    """
    Tracks all camel positions on the board.

    Maps space number (0-15 for track, 16+ for finished) to the stack on that space.
    Space 0 is not used (camels start at 1-3).
    """
    # Mapping from space number to stack
    stacks: Tuple[CamelStack, ...]  # Index = space number

    @classmethod
    def create_empty(cls, num_spaces: int = 20) -> "CamelPositions":
        """Create empty positions with given number of spaces."""
        return cls(stacks=tuple(CamelStack.empty() for _ in range(num_spaces)))

    def get_stack(self, space: int) -> CamelStack:
        """Get the stack at a given space."""
        if 0 <= space < len(self.stacks):
            return self.stacks[space]
        return CamelStack.empty()

    def find_camel(self, camel: CamelColor) -> Tuple[int, int] | None:
        """
        Find a camel's position.
        Returns (space, height) where height is position in stack (0 = bottom).
        """
        for space, stack in enumerate(self.stacks):
            height = stack.position_of(camel)
            if height is not None:
                return (space, height)
        return None

    def get_camel_space(self, camel: CamelColor) -> int | None:
        """Get just the space number where a camel is located."""
        result = self.find_camel(camel)
        return result[0] if result else None

    def place_camel(self, camel: CamelColor, space: int) -> "CamelPositions":
        """
        Place a camel on a specific space (for initial setup).

        The camel is placed on top of any existing camels at that space.
        """
        if space < 0 or space >= len(self.stacks):
            raise ValueError(f"Invalid space: {space}")

        # Get existing stack at destination
        dest_stack = self.stacks[space]

        # Add camel on top
        new_dest_stack = dest_stack.add_on_top(CamelStack.from_camels(camel))

        # Build new stacks
        new_stacks = list(self.stacks)
        new_stacks[space] = new_dest_stack

        return CamelPositions(stacks=tuple(new_stacks))

    def move_camel(
        self,
        camel: CamelColor,
        spaces: int,
        place_underneath: bool = False
    ) -> "CamelPositions":
        """
        Move a camel and all camels on top of it.

        Args:
            camel: The camel to move
            spaces: Number of spaces to move (positive = forward, negative = backward)
            place_underneath: If True, place moving stack underneath existing camels
                            (used for booing spectator tiles)

        Returns:
            New CamelPositions with the move applied
        """
        # Find current position
        pos = self.find_camel(camel)
        if pos is None:
            # Camel not on board - place it at the target space
            target = max(1, spaces)  # Ensure at least space 1
            return self.place_camel(camel, target)

        current_space, _ = pos
        new_space = current_space + spaces

        # Handle board boundaries
        # For racing camels going forward, space 17+ means finished
        # For crazy camels going backward, space 0 or below wraps or stays
        if new_space < 1:
            new_space = 1  # Can't go below space 1
        # Note: We don't cap at 16 here - let board.py handle finish detection

        # Get the current stack at origin
        origin_stack = self.stacks[current_space]

        # Split the stack - moving camel and everything above it
        remaining_at_origin, moving_stack = origin_stack.remove_camels_from(camel)

        # Get the stack at destination (if within bounds)
        if new_space < len(self.stacks):
            dest_stack = self.stacks[new_space]
        else:
            dest_stack = CamelStack.empty()

        # Combine stacks at destination
        if place_underneath:
            # Moving stack goes underneath existing camels
            new_dest_stack = dest_stack.add_underneath(moving_stack)
        else:
            # Moving stack goes on top of existing camels
            new_dest_stack = dest_stack.add_on_top(moving_stack)

        # Build new stacks tuple
        new_stacks = list(self.stacks)

        # Extend if needed
        while len(new_stacks) <= new_space:
            new_stacks.append(CamelStack.empty())

        new_stacks[current_space] = remaining_at_origin
        new_stacks[new_space] = new_dest_stack

        return CamelPositions(stacks=tuple(new_stacks))

    def get_ranking(self) -> List[CamelColor]:
        """
        Get racing camels ranked from 1st to last place.

        Ranking rules:
        - Camel on highest space is ahead
        - If tied on space, camel higher in stack is ahead
        - Crazy camels are ignored for ranking
        """
        ranked: List[Tuple[int, int, CamelColor]] = []

        for space in range(len(self.stacks) - 1, -1, -1):
            stack = self.stacks[space]
            for height, camel in enumerate(stack.camels):
                if camel.is_racing_camel():
                    # Use negative space and height for sorting (higher = better)
                    ranked.append((-space, -height, camel))

        # Sort by space (descending), then height (descending)
        ranked.sort()

        return [camel for _, _, camel in ranked]

    def is_camel_finished(self, camel: CamelColor, finish_line: int = 17) -> bool:
        """Check if a camel has crossed the finish line."""
        space = self.get_camel_space(camel)
        return space is not None and space >= finish_line

    def any_camel_finished(self, finish_line: int = 17) -> bool:
        """Check if any racing camel has crossed the finish line."""
        for camel in RACING_CAMELS:
            if self.is_camel_finished(camel, finish_line):
                return True
        return False

    def has_racing_camels_on_back(self, crazy_camel: CamelColor) -> bool:
        """
        Check if a crazy camel has any racing camels on its back.

        Used for the crazy camel priority rule: if only one crazy camel
        carries racing camels, that one must move.
        """
        if not crazy_camel.is_crazy_camel():
            return False

        pos = self.find_camel(crazy_camel)
        if pos is None:
            return False

        space, _ = pos
        stack = self.get_stack(space)

        # Get all camels above the crazy camel
        camels_above = stack.get_camels_above(crazy_camel)

        # Check if any of them (excluding the crazy camel itself) are racing camels
        for camel in camels_above:
            if camel != crazy_camel and camel.is_racing_camel():
                return True
        return False

    def get_crazy_camel_to_move(self, grey_die_camel: CamelColor) -> CamelColor:
        """
        Determine which crazy camel should move based on the rules.

        Rules (from rulebook page 4):
        1. If only one crazy camel has racing camels on its back, move that one.
        2. If crazy camels are stacked directly (no racing camels between),
           move the one on top.
        3. Otherwise, move the camel indicated by the grey die.

        Args:
            grey_die_camel: The crazy camel color shown on the grey die

        Returns:
            The crazy camel that should actually move
        """
        white_has_racers = self.has_racing_camels_on_back(CamelColor.WHITE)
        black_has_racers = self.has_racing_camels_on_back(CamelColor.BLACK)

        # Rule 1: If only one has racing camels, move that one
        if white_has_racers and not black_has_racers:
            return CamelColor.WHITE
        if black_has_racers and not white_has_racers:
            return CamelColor.BLACK

        # Rule 2: If they're stacked directly (no racers between), move top one
        white_pos = self.find_camel(CamelColor.WHITE)
        black_pos = self.find_camel(CamelColor.BLACK)

        if white_pos and black_pos and white_pos[0] == black_pos[0]:
            # Both on same space - check if stacked directly
            space = white_pos[0]
            stack = self.get_stack(space)

            white_height = stack.position_of(CamelColor.WHITE)
            black_height = stack.position_of(CamelColor.BLACK)

            if white_height is not None and black_height is not None:
                # Check if they're adjacent in the stack (no camels between)
                lower_height = min(white_height, black_height)
                upper_height = max(white_height, black_height)

                # Check if there are any racing camels between them
                has_racers_between = False
                for h in range(lower_height + 1, upper_height):
                    if stack.camels[h].is_racing_camel():
                        has_racers_between = True
                        break

                if not has_racers_between:
                    # Move the one on top
                    if white_height > black_height:
                        return CamelColor.WHITE
                    else:
                        return CamelColor.BLACK

        # Default: move the camel indicated by the grey die
        return grey_die_camel


def create_initial_positions(
    dice_rolls: List[Tuple[CamelColor, int]],
    crazy_positions: List[Tuple[CamelColor, int]] | None = None
) -> CamelPositions:
    """
    Create initial camel positions from setup dice rolls.

    Args:
        dice_rolls: List of (camel_color, roll_value) for racing camels
        crazy_positions: List of (camel_color, space) for crazy camels
    """
    positions = CamelPositions.create_empty()

    # Place racing camels based on dice rolls
    # Camels rolling 1 go to space 1, rolling 2 go to space 2, etc.
    for camel, roll in dice_rolls:
        if camel.is_racing_camel():
            positions = positions.move_camel(camel, roll)

    # Place crazy camels at their starting positions
    if crazy_positions:
        for camel, space in crazy_positions:
            if camel.is_crazy_camel():
                # Crazy camels start at spaces 14-16 based on grey die
                positions = positions.place_camel(camel, space)

    return positions
