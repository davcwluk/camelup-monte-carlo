"""Board and track representation for Camel Up."""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from .camel import CamelPositions, CamelColor, CamelStack, RACING_CAMELS


# Board constants
TRACK_LENGTH = 16  # Spaces 1-16, finish line after 16
FINISH_LINE = 17   # Space number considered "finished"

# Crazy camel starting positions based on grey die roll
CRAZY_START_POSITIONS = {
    1: 16,
    2: 15,
    3: 14,
}


@dataclass(frozen=True)
class SpectatorTile:
    """A spectator tile that modifies camel movement."""
    owner: int  # Player index who placed the tile
    is_cheering: bool  # True = +1 (cheering), False = -1 (booing)

    @property
    def movement_modifier(self) -> int:
        """Get the movement modifier (+1 or -1)."""
        return 1 if self.is_cheering else -1

    @property
    def place_underneath(self) -> bool:
        """Whether camels landing here go underneath existing camels."""
        return not self.is_cheering  # Booing tiles place underneath


@dataclass(frozen=True)
class Board:
    """
    Represents the game board state.

    Tracks:
    - Camel positions on the track
    - Spectator tile placements
    """
    camel_positions: CamelPositions
    # Spectator tiles: maps space number to tile
    spectator_tiles: Dict[int, SpectatorTile] = field(default_factory=dict)

    @classmethod
    def create_empty(cls) -> "Board":
        """Create an empty board."""
        return cls(
            camel_positions=CamelPositions.create_empty(TRACK_LENGTH + 5),
            spectator_tiles={}
        )

    def get_stack_at(self, space: int) -> CamelStack:
        """Get the camel stack at a given space."""
        return self.camel_positions.get_stack(space)

    def get_spectator_tile(self, space: int) -> SpectatorTile | None:
        """Get the spectator tile at a given space, if any."""
        return self.spectator_tiles.get(space)

    def can_place_spectator_tile(self, space: int, player: int) -> bool:
        """
        Check if a spectator tile can be placed at a given space.

        Rules:
        - Cannot place on space 1
        - Cannot place on a space with camels
        - Cannot place adjacent to another spectator tile
        - Cannot place on a space that already has a tile
        """
        if space < 2 or space > TRACK_LENGTH:
            return False

        # Check if space has camels
        if self.get_stack_at(space):
            return False

        # Check if space already has a tile (from another player)
        if space in self.spectator_tiles and self.spectator_tiles[space].owner != player:
            return False

        # Check adjacent spaces for other players' tiles
        if (space - 1) in self.spectator_tiles and self.spectator_tiles[space - 1].owner != player:
            return False
        if (space + 1) in self.spectator_tiles and self.spectator_tiles[space + 1].owner != player:
            return False

        return True

    def place_spectator_tile(
        self,
        space: int,
        player: int,
        is_cheering: bool
    ) -> "Board":
        """
        Place a spectator tile on the board.

        Returns new board state with tile placed.
        """
        if not self.can_place_spectator_tile(space, player):
            raise ValueError(f"Cannot place spectator tile at space {space}")

        # Remove any existing tile owned by this player
        new_tiles = {
            s: tile for s, tile in self.spectator_tiles.items()
            if tile.owner != player
        }

        # Add new tile
        new_tiles[space] = SpectatorTile(owner=player, is_cheering=is_cheering)

        return Board(
            camel_positions=self.camel_positions,
            spectator_tiles=new_tiles
        )

    def remove_spectator_tile(self, space: int) -> "Board":
        """Remove a spectator tile from a space."""
        new_tiles = {s: t for s, t in self.spectator_tiles.items() if s != space}
        return Board(
            camel_positions=self.camel_positions,
            spectator_tiles=new_tiles
        )

    def move_camel(
        self,
        camel: CamelColor,
        spaces: int
    ) -> Tuple["Board", int | None]:
        """
        Move a camel and handle spectator tile effects.

        Returns:
            Tuple of (new_board, spectator_tile_owner) where owner is None
            if no spectator tile was triggered.
        """
        # Find current position
        current_pos = self.camel_positions.get_camel_space(camel)
        if current_pos is None:
            return self, None

        # Calculate target space before spectator tile
        target_space = current_pos + spaces

        # Check for spectator tile at target
        tile = self.get_spectator_tile(target_space)
        tile_owner = None

        if tile:
            # Apply tile modifier
            target_space += tile.movement_modifier
            tile_owner = tile.owner
            place_underneath = tile.place_underneath
        else:
            place_underneath = False

        # Ensure we don't go below space 1
        if target_space < 1:
            target_space = 1

        # Move the camel
        new_positions = self.camel_positions.move_camel(
            camel,
            target_space - current_pos,  # Actual spaces to move
            place_underneath=place_underneath
        )

        new_board = Board(
            camel_positions=new_positions,
            spectator_tiles=self.spectator_tiles
        )

        return new_board, tile_owner

    def is_game_over(self) -> bool:
        """Check if any racing camel has crossed the finish line."""
        return self.camel_positions.any_camel_finished(FINISH_LINE)

    def get_ranking(self) -> List[CamelColor]:
        """Get racing camels ranked from 1st to last."""
        return self.camel_positions.get_ranking()

    def get_leader(self) -> CamelColor | None:
        """Get the current race leader."""
        ranking = self.get_ranking()
        return ranking[0] if ranking else None

    def get_last_place(self) -> CamelColor | None:
        """Get the camel in last place."""
        ranking = self.get_ranking()
        return ranking[-1] if ranking else None

    def get_valid_spectator_spaces(self, player: int) -> List[int]:
        """Get all spaces where a player can place their spectator tile."""
        return [
            space for space in range(2, TRACK_LENGTH + 1)
            if self.can_place_spectator_tile(space, player)
        ]

    def clear_all_spectator_tiles(self) -> "Board":
        """Remove all spectator tiles (done at end of leg)."""
        return Board(
            camel_positions=self.camel_positions,
            spectator_tiles={}
        )

    def __str__(self) -> str:
        """String representation of the board for debugging."""
        lines = []
        for space in range(1, TRACK_LENGTH + 1):
            stack = self.get_stack_at(space)
            tile = self.get_spectator_tile(space)

            space_str = f"[{space:2d}]"

            if stack:
                camels_str = ",".join(c.value[0].upper() for c in stack.camels)
                space_str += f" {camels_str}"
            else:
                space_str += " ---"

            if tile:
                tile_str = "+1" if tile.is_cheering else "-1"
                space_str += f" (tile:{tile_str})"

            lines.append(space_str)

        # Show finished camels
        for space in range(FINISH_LINE, FINISH_LINE + 5):
            stack = self.get_stack_at(space)
            if stack:
                camels_str = ",".join(c.value[0].upper() for c in stack.camels)
                lines.append(f"[FIN] {camels_str}")

        return "\n".join(lines)
