"""Tests for spectator tile mechanics."""

import pytest
from src.game.board import Board, SpectatorTile, TRACK_LENGTH
from src.game.camel import CamelColor, CamelPositions


class TestSpectatorTilePlacement:
    """Tests for spectator tile placement rules."""

    def test_cannot_place_tile_on_space_1(self):
        """Cannot place spectator tile on space 1."""
        board = Board.create_empty()
        assert not board.can_place_spectator_tile(space=1, player=0)

    def test_cannot_place_tile_on_space_0(self):
        """Cannot place spectator tile on space 0 (invalid)."""
        board = Board.create_empty()
        assert not board.can_place_spectator_tile(space=0, player=0)

    def test_cannot_place_tile_beyond_track(self):
        """Cannot place spectator tile beyond the track."""
        board = Board.create_empty()
        assert not board.can_place_spectator_tile(space=TRACK_LENGTH + 1, player=0)

    def test_can_place_tile_on_empty_space(self):
        """Can place spectator tile on empty space (2-16)."""
        board = Board.create_empty()
        for space in range(2, TRACK_LENGTH + 1):
            assert board.can_place_spectator_tile(space=space, player=0)

    def test_cannot_place_tile_on_space_with_camels(self):
        """Cannot place spectator tile on space occupied by camels."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 5)
        board = Board(camel_positions=positions, spectator_tiles={})

        assert not board.can_place_spectator_tile(space=5, player=0)
        assert board.can_place_spectator_tile(space=6, player=0)  # Adjacent is ok

    def test_cannot_place_tile_adjacent_to_another_tile(self):
        """Cannot place spectator tile adjacent to another spectator tile."""
        board = Board.create_empty()
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Cannot place on spaces 4 or 6 (adjacent to space 5)
        assert not board.can_place_spectator_tile(space=4, player=1)
        assert not board.can_place_spectator_tile(space=6, player=1)

        # Can place on spaces 3 or 7 (not adjacent)
        assert board.can_place_spectator_tile(space=3, player=1)
        assert board.can_place_spectator_tile(space=7, player=1)

    def test_cannot_place_tile_on_existing_tile(self):
        """Cannot place spectator tile on space that already has a tile."""
        board = Board.create_empty()
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        assert not board.can_place_spectator_tile(space=5, player=1)

    def test_can_move_own_tile_to_adjacent_space(self):
        """Player can move their own tile to an adjacent space."""
        board = Board.create_empty()
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Player 0 should be able to place adjacent to their own tile
        assert board.can_place_spectator_tile(space=4, player=0)
        assert board.can_place_spectator_tile(space=6, player=0)

        # But player 1 still cannot
        assert not board.can_place_spectator_tile(space=4, player=1)
        assert not board.can_place_spectator_tile(space=6, player=1)

    def test_can_move_own_tile_to_same_space(self):
        """Player can re-place their tile on the same space (e.g., switch sides)."""
        board = Board.create_empty()
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Player 0 can place on the same space (switch to booing)
        assert board.can_place_spectator_tile(space=5, player=0)
        board = board.place_spectator_tile(space=5, player=0, is_cheering=False)
        assert board.get_spectator_tile(5).is_cheering is False

    def test_tile_has_two_sides(self):
        """Spectator tile can be placed cheering (+1) or booing (-1)."""
        cheering_tile = SpectatorTile(owner=0, is_cheering=True)
        booing_tile = SpectatorTile(owner=0, is_cheering=False)

        assert cheering_tile.movement_modifier == 1
        assert booing_tile.movement_modifier == -1

        assert not cheering_tile.place_underneath
        assert booing_tile.place_underneath

    def test_moving_tile_removes_from_old_position(self):
        """When a player places their tile again, it moves from old position."""
        board = Board.create_empty()

        # Player 0 places tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)
        assert board.get_spectator_tile(5) is not None

        # Player 0 places tile at space 10 (should remove from space 5)
        board = board.place_spectator_tile(space=10, player=0, is_cheering=False)

        assert board.get_spectator_tile(5) is None  # Old position cleared
        assert board.get_spectator_tile(10) is not None  # New position has tile
        assert board.get_spectator_tile(10).is_cheering is False


class TestSpectatorTileEffects:
    """Tests for spectator tile effects on camel movement."""

    def test_cheering_tile_adds_one_space(self):
        """Cheering tile causes camel to move +1 extra space."""
        # Place camel at space 3
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place cheering tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Move blue camel 2 spaces (3 -> 5, but tile adds +1, so 3 -> 6)
        new_board, tile_owner = board.move_camel(CamelColor.BLUE, 2)

        assert new_board.camel_positions.get_camel_space(CamelColor.BLUE) == 6
        assert tile_owner == 0  # Player 0 owns the tile

    def test_booing_tile_subtracts_one_space(self):
        """Booing tile causes camel to move -1 space (backward)."""
        # Place camel at space 3
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place booing tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=False)

        # Move blue camel 2 spaces (3 -> 5, but tile subtracts 1, so 3 -> 4)
        new_board, tile_owner = board.move_camel(CamelColor.BLUE, 2)

        assert new_board.camel_positions.get_camel_space(CamelColor.BLUE) == 4
        assert tile_owner == 0

    def test_cheering_tile_lands_on_top(self):
        """Camel landing via cheering tile goes ON TOP of existing camels."""
        # Place red camel at space 6
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.RED, 6)
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place cheering tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Move blue 2 spaces (3 -> 5 + 1 = 6, landing on red)
        new_board, _ = board.move_camel(CamelColor.BLUE, 2)

        # Blue should be on top of red at space 6
        stack = new_board.camel_positions.get_stack(6)
        assert stack.bottom() == CamelColor.RED
        assert stack.top() == CamelColor.BLUE

    def test_booing_tile_lands_underneath(self):
        """Camel landing via booing tile goes UNDERNEATH existing camels."""
        # Place red camel at space 4
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.RED, 4)
        positions = positions.place_camel(CamelColor.BLUE, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place booing tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=False)

        # Move blue 2 spaces (3 -> 5 - 1 = 4, landing under red)
        new_board, _ = board.move_camel(CamelColor.BLUE, 2)

        # Blue should be underneath red at space 4
        stack = new_board.camel_positions.get_stack(4)
        assert stack.bottom() == CamelColor.BLUE  # Blue went underneath
        assert stack.top() == CamelColor.RED

    def test_tile_owner_receives_one_coin(self):
        """Tile owner receives 1 coin when any camel lands on their tile."""
        from src.game.spectator import get_tile_payout
        assert get_tile_payout() == 1

    def test_tile_effect_with_stack(self):
        """Tile effect applies to entire moving stack."""
        # Stack: Blue (bottom), Green (top) at space 3
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Place cheering tile at space 5
        board = board.place_spectator_tile(space=5, player=0, is_cheering=True)

        # Move blue 2 spaces (carries green), tile adds +1
        new_board, tile_owner = board.move_camel(CamelColor.BLUE, 2)

        # Both camels should be at space 6
        assert new_board.camel_positions.get_camel_space(CamelColor.BLUE) == 6
        assert new_board.camel_positions.get_camel_space(CamelColor.GREEN) == 6
        assert tile_owner == 0
