"""Spectator tile mechanics for Camel Up.

This module re-exports spectator tile functionality from board.py
and provides additional utility functions.
"""

from .board import SpectatorTile, Board

__all__ = ["SpectatorTile", "apply_spectator_effect"]


def apply_spectator_effect(
    base_movement: int,
    tile: SpectatorTile | None
) -> tuple[int, bool]:
    """
    Calculate the final movement after applying spectator tile effect.

    Args:
        base_movement: The original movement from the die roll
        tile: The spectator tile at the landing space, or None

    Returns:
        Tuple of (final_movement, place_underneath)
        - final_movement: Movement including tile modifier
        - place_underneath: Whether to place under existing camels
    """
    if tile is None:
        return base_movement, False

    final_movement = base_movement + tile.movement_modifier
    return final_movement, tile.place_underneath


def get_tile_payout() -> int:
    """Get the coin payout when a camel lands on your spectator tile."""
    return 1
