"""Tests for game logger and renderer."""

import os
import tempfile

import pytest

from src.game.game import GameState, play_game
from src.game.camel import CamelColor, CamelPositions, CamelStack, create_initial_positions
from src.game.board import Board, SpectatorTile, TRACK_LENGTH
from src.game.dice import Pyramid, DieColor
from src.game.betting import BettingState, PlayerState
from src.logging.renderer import (
    render_board, render_scores, render_ranking, render_pyramid,
)
from src.logging.game_logger import GameLogger
from src.agents import RandomAgent, GreedyAgent


class TestRenderBoard:
    """Tests for render_board()."""

    def test_render_board_spread(self):
        """Camels on separate spaces show correctly."""
        positions = create_initial_positions([
            (CamelColor.RED, 1),
            (CamelColor.BLUE, 2),
            (CamelColor.GREEN, 3),
            (CamelColor.YELLOW, 4),
            (CamelColor.PURPLE, 5),
        ])
        board = Board(camel_positions=positions, spectator_tiles={})
        result = render_board(board)
        assert "[1:Red]" in result
        assert "[2:Blu]" in result
        assert "[3:Grn]" in result
        assert "[4:Yel]" in result
        assert "[5:Pur]" in result
        # Empty spaces
        assert "[6:]" in result

    def test_render_board_stacked(self):
        """Camels sharing a space show bottom to top."""
        positions = create_initial_positions([
            (CamelColor.RED, 2),
            (CamelColor.BLUE, 2),
            (CamelColor.GREEN, 3),
            (CamelColor.YELLOW, 3),
            (CamelColor.PURPLE, 3),
        ])
        board = Board(camel_positions=positions, spectator_tiles={})
        result = render_board(board)
        # Red placed first at space 2, Blue on top
        assert "[2:Red>Blu]" in result
        # Green, Yellow, Purple stacked at space 3
        assert "[3:Grn>Yel>Pur]" in result

    def test_render_board_crazy_camels(self):
        """Crazy camels show with * prefix."""
        positions = create_initial_positions(
            [(CamelColor.RED, 1), (CamelColor.BLUE, 2),
             (CamelColor.GREEN, 3), (CamelColor.YELLOW, 4),
             (CamelColor.PURPLE, 5)],
            crazy_positions=[
                (CamelColor.WHITE, 14),
                (CamelColor.BLACK, 16),
            ]
        )
        board = Board(camel_positions=positions, spectator_tiles={})
        result = render_board(board)
        assert "*Wht" in result
        assert "*Blk" in result
        assert "[14:*Wht]" in result
        assert "[16:*Blk]" in result

    def test_render_board_spectator_tiles(self):
        """Spectator tiles appear on a separate line."""
        positions = create_initial_positions([
            (CamelColor.RED, 1), (CamelColor.BLUE, 2),
            (CamelColor.GREEN, 3), (CamelColor.YELLOW, 4),
            (CamelColor.PURPLE, 5),
        ])
        tiles = {
            8: SpectatorTile(owner=0, is_cheering=True),
        }
        board = Board(camel_positions=positions, spectator_tiles=tiles)
        result = render_board(board)
        assert "Spectator tiles:" in result
        assert "space 8 cheering(+1) by P0" in result


class TestRenderRanking:
    """Tests for render_ranking()."""

    def test_render_ranking(self):
        """Ranking text format is correct."""
        positions = create_initial_positions([
            (CamelColor.RED, 3),
            (CamelColor.BLUE, 1),
            (CamelColor.GREEN, 2),
            (CamelColor.YELLOW, 5),
            (CamelColor.PURPLE, 4),
        ])
        board = Board(camel_positions=positions, spectator_tiles={})
        result = render_ranking(board)
        assert result.startswith("Ranking: ")
        assert "Yellow 1st" in result
        assert "Purple 2nd" in result
        assert "Red 3rd" in result
        assert "Green 4th" in result
        assert "Blue 5th" in result


class TestRenderScores:
    """Tests for render_scores()."""

    def test_render_scores(self):
        """Score format is correct."""
        players = (PlayerState(coins=3), PlayerState(coins=7))
        result = render_scores(players)
        assert result == "Scores: P0=3, P1=7"


class TestRenderPyramid:
    """Tests for render_pyramid()."""

    def test_render_pyramid_full(self):
        """Full pyramid shows all dice."""
        pyramid = Pyramid()
        result = render_pyramid(pyramid)
        assert "Remaining dice:" in result
        assert "Grey: available" in result
        # All 5 racing dice
        for color in ("Blue", "Green", "Yellow", "Red", "Purple"):
            assert color in result

    def test_render_pyramid_partial(self):
        """Partial pyramid shows remaining dice."""
        pyramid = Pyramid(
            remaining=frozenset({DieColor.BLUE, DieColor.RED}),
            grey_rolled=True,
        )
        result = render_pyramid(pyramid)
        assert "Blue" in result
        assert "Red" in result
        assert "Green" not in result
        assert "Grey: rolled" in result


class TestGameLoggerFullGame:
    """Integration tests for GameLogger with full games."""

    def test_logger_full_game(self):
        """Play a game with logger, verify output file has expected sections."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            logger = GameLogger(output_path=log_path, console=False)
            agents = [RandomAgent(seed=1), RandomAgent(seed=2)]
            state, history = play_game(
                num_players=2, agent_functions=agents, seed=42, logger=logger
            )

            # Read back the log
            with open(log_path) as f:
                log_text = f.read()

            assert len(log_text) > 0
            assert "GAME START" in log_text
            assert "GAME END" in log_text
            assert "Leg" in log_text
            assert "Turn" in log_text
            assert "Board:" in log_text
            assert "Scores:" in log_text
        finally:
            os.unlink(log_path)

    def test_logger_captures_die_rolls(self):
        """Die roll info appears in log for pyramid ticket actions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            logger = GameLogger(output_path=log_path, console=False)
            agents = [RandomAgent(seed=10), RandomAgent(seed=20)]
            play_game(num_players=2, agent_functions=agents, seed=99, logger=logger)

            with open(log_path) as f:
                log_text = f.read()

            # At least one die roll should be logged (RandomAgent rolls sometimes)
            assert "Die:" in log_text
            assert "rolled" in log_text
        finally:
            os.unlink(log_path)

    def test_logger_captures_agent_evs(self):
        """Top 3 EVs appear in log for GreedyAgent turns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            logger = GameLogger(output_path=log_path, console=False)
            # Use fast_mode to keep test quick
            agents = [
                GreedyAgent(seed=1, fast_mode=True),
                RandomAgent(seed=2),
            ]
            play_game(num_players=2, agent_functions=agents, seed=42, logger=logger)

            with open(log_path) as f:
                log_text = f.read()

            # GreedyAgent should have EV info logged
            assert "EVs:" in log_text
        finally:
            os.unlink(log_path)

    def test_logger_no_file(self):
        """Logger with no output_path and console=False produces no errors."""
        logger = GameLogger(output_path=None, console=False)
        agents = [RandomAgent(seed=1), RandomAgent(seed=2)]
        state, history = play_game(
            num_players=2, agent_functions=agents, seed=42, logger=logger
        )
        assert state.is_game_over

    def test_logger_leg_end_detected(self):
        """Logger detects and logs leg endings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            logger = GameLogger(output_path=log_path, console=False)
            agents = [RandomAgent(seed=1), RandomAgent(seed=2)]
            play_game(num_players=2, agent_functions=agents, seed=42, logger=logger)

            with open(log_path) as f:
                log_text = f.read()

            # Game should have at least one leg end
            assert "LEG" in log_text
            assert "END" in log_text
            assert "Ranking:" in log_text
        finally:
            os.unlink(log_path)
