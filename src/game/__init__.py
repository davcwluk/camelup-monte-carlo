"""Camel Up game engine."""

from .camel import CamelColor, CamelStack, CamelPositions, RACING_CAMELS, CRAZY_CAMELS
from .dice import DieColor, DieRoll, Pyramid, RACING_DIE_FACES
from .board import Board, SpectatorTile, TRACK_LENGTH, FINISH_LINE
from .betting import (
    BettingTicket, BettingState, PlayerState,
    calculate_leg_scores, calculate_overall_scores
)
from .game import GameState, Action, ActionType, play_game

__all__ = [
    # Camels
    "CamelColor", "CamelStack", "CamelPositions", "RACING_CAMELS", "CRAZY_CAMELS",
    # Dice
    "DieColor", "DieRoll", "Pyramid", "RACING_DIE_FACES",
    # Board
    "Board", "SpectatorTile", "TRACK_LENGTH", "FINISH_LINE",
    # Betting
    "BettingTicket", "BettingState", "PlayerState",
    "calculate_leg_scores", "calculate_overall_scores",
    # Game
    "GameState", "Action", "ActionType", "play_game",
]
