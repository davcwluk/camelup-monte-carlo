"""Human-readable game logger for debugging and rule verification."""

import random

from .renderer import (
    render_board, render_scores, render_ranking, render_pyramid,
    _CAMEL_FULL_NAMES, _camel_display,
)
from ..game.camel import CamelColor, RACING_CAMELS
from ..game.board import Board, TRACK_LENGTH, FINISH_LINE, CRAZY_START_POSITIONS
from ..game.dice import DieColor, DieRoll, roll_racing_die, roll_grey_die
from ..game.game import ActionType
from ..game.betting import calculate_leg_scores


class GameLogger:
    """Logs a game in human-readable format for debugging."""

    def __init__(self, output_path=None, console=True):
        """
        Args:
            output_path: Path to write log file (None = no file).
            console: Also print to stdout.
        """
        self.output_path = output_path
        self.console = console
        self._file = None
        if output_path:
            self._file = open(output_path, "w")

    def close(self):
        """Close the log file if open."""
        if self._file:
            self._file.close()
            self._file = None

    def log(self, text):
        """Write a line to the log."""
        if self.console:
            print(text)
        if self._file:
            self._file.write(text + "\n")
            self._file.flush()

    def _log_blank(self):
        self.log("")

    def log_game_start(self, state, seed, agents):
        """Log the initial game setup."""
        num_players = state.get_num_players()
        seed_str = f"seed={seed}" if seed is not None else "seed=None"
        self.log(f"========== GAME START ({seed_str}, {num_players} players) ==========")

        # Replay seed to capture initial placement rolls
        if seed is not None:
            rng = random.Random(seed)
            self.log("Initial placement:")
            for camel in RACING_CAMELS:
                die_color = DieColor[camel.name]
                roll = roll_racing_die(die_color, rng)
                space = roll.value
                # Check if another camel is already on that space
                stack = state.board.get_stack_at(space)
                stack_note = ""
                if len(stack) > 1 and camel in stack.camels:
                    idx = stack.position_of(camel)
                    if idx > 0:
                        below = stack.camels[idx - 1]
                        stack_note = f" (on top of {_CAMEL_FULL_NAMES[below]})"
                self.log(f"  {_CAMEL_FULL_NAMES[camel]} rolled {roll.value} -> space {space}{stack_note}")

            # Grey die rolls for crazy camels
            grey_roll_1 = roll_grey_die(rng)
            grey_roll_2 = roll_grey_die(rng)
            white_space = CRAZY_START_POSITIONS[grey_roll_1.value]
            black_space = CRAZY_START_POSITIONS[grey_roll_2.value]
            self.log(f"  White -> space {white_space}, Black -> space {black_space}")

        self._log_blank()
        self.log(render_board(state.board))
        self.log(render_scores(state.players))
        self.log(render_pyramid(state.pyramid))
        self._log_blank()
        self.log(f"---------- Leg {state.leg_number} ----------")
        self._log_blank()

    def log_turn(self, turn_num, old_state, action, new_state, agent):
        """Log a single turn."""
        player = old_state.current_player
        agent_name = getattr(agent, "name", agent.__class__.__name__)
        coins = old_state.players[player].coins
        self.log(f"Turn {turn_num} | Player {player} ({agent_name}) | Coins: {coins}")

        # Action description
        self.log(f"  Action: {action}")

        # Agent EV reasoning (if available)
        evs = getattr(agent, "last_action_evs", None)
        if evs:
            ev_parts = []
            for act, ev in evs:
                ev_parts.append(f"{_action_short(act)}={ev:.2f}")
            self.log(f"  EVs: {', '.join(ev_parts)}")

        # Die roll info
        die_roll = new_state.last_die_roll
        if die_roll is not None:
            self._log_die_roll(die_roll, old_state.board, new_state.board)

        # Spectator tile trigger detection
        if action.action_type == ActionType.TAKE_PYRAMID_TICKET:
            self._log_spectator_trigger(old_state, new_state)

        # Board after move (only for actions that change the board)
        if action.action_type in (ActionType.TAKE_PYRAMID_TICKET, ActionType.PLACE_SPECTATOR_TILE):
            self.log(f"  {render_board(new_state.board)}")

        self._log_blank()

    def _log_die_roll(self, die_roll, old_board, new_board):
        """Log die roll and resulting camel movement."""
        if die_roll.color == DieColor.GREY:
            camel_name = die_roll.crazy_camel.capitalize()
            self.log(f"  Die: Grey rolled {die_roll.value} ({camel_name})")
            # Find which crazy camel actually moved
            for camel in (CamelColor.WHITE, CamelColor.BLACK):
                old_space = old_board.camel_positions.get_camel_space(camel)
                new_space = new_board.camel_positions.get_camel_space(camel)
                if old_space != new_space:
                    self.log(f"    {_CAMEL_FULL_NAMES[camel]} moves {old_space}->{new_space}")
        else:
            color_name = die_roll.color.value.capitalize()
            camel = CamelColor[die_roll.color.name]
            old_space = old_board.camel_positions.get_camel_space(camel)
            new_space = new_board.camel_positions.get_camel_space(camel)
            self.log(f"  Die: {color_name} rolled {die_roll.value} -> {color_name} moves {old_space}->{new_space}")

    def _log_spectator_trigger(self, old_state, new_state):
        """Detect and log spectator tile triggers from die roll and board state."""
        die_roll = new_state.last_die_roll
        if die_roll is None:
            return

        # Determine natural target space (before spectator tile modifier)
        if die_roll.color == DieColor.GREY:
            # Use priority rules to find which crazy camel actually moved
            grey_die_camel = (CamelColor.WHITE if die_roll.crazy_camel == "white"
                              else CamelColor.BLACK)
            camel = old_state.board.camel_positions.get_crazy_camel_to_move(grey_die_camel)
            old_space = old_state.board.camel_positions.get_camel_space(camel)
            natural_target = old_space - die_roll.value
        else:
            camel = CamelColor[die_roll.color.name]
            old_space = old_state.board.camel_positions.get_camel_space(camel)
            natural_target = old_space + die_roll.value

        if natural_target < 1:
            natural_target = 1

        tile = old_state.board.get_spectator_tile(natural_target)
        if tile:
            self.log(f"  Spectator tile triggered: P{tile.owner} earns 1 coin")

    def log_leg_end(self, leg_num, old_state, new_state, last_action=None):
        """Log end-of-leg scoring."""
        self.log(f"========== LEG {leg_num} END ==========")
        self.log(render_ranking(new_state.board))

        # Reconstruct the betting state that was used for scoring.
        # old_state.betting doesn't include the leg-ending turn's action
        # (e.g., a pyramid ticket taken on the last turn of the leg).
        betting = old_state.betting
        if last_action and last_action.action_type == ActionType.TAKE_PYRAMID_TICKET:
            betting = betting.take_pyramid_ticket(old_state.current_player)

        ranking = new_state.board.get_ranking()
        first = ranking[0] if ranking else None
        second = ranking[1] if len(ranking) > 1 else None

        if first and second:
            leg_scores = calculate_leg_scores(betting, first, second)
            self.log("Scoring:")
            for i in range(len(old_state.players)):
                parts = []
                # Leg betting tickets
                for ticket in betting.player_tickets[i]:
                    if ticket.camel == first:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[ticket.camel]} ({ticket.value}-ticket) -> 1st -> +{ticket.value}")
                    elif ticket.camel == second:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[ticket.camel]} ({ticket.value}-ticket) -> 2nd -> +1")
                    else:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[ticket.camel]} ({ticket.value}-ticket) -> other -> -1")

                # Pyramid tickets
                pyr_count = betting.player_pyramid_tickets[i]
                if pyr_count > 0:
                    parts.append(f"{pyr_count} pyramid ticket{'s' if pyr_count > 1 else ''} -> +{pyr_count}")

                if parts:
                    detail = "; ".join(parts)
                    self.log(f"  P{i}: {detail} (net {leg_scores[i]:+d})")
                else:
                    self.log(f"  P{i}: no bets (net {leg_scores[i]:+d})")

        self.log(render_scores(new_state.players))
        self._log_blank()

        # Start new leg header
        self.log(f"---------- Leg {new_state.leg_number} ----------")
        self._log_blank()

    def log_game_end(self, state):
        """Log final game results."""
        self.log("========== GAME END ==========")

        ranking = state.board.get_ranking()
        # Find which camel crossed the finish line
        for camel in ranking:
            space = state.board.camel_positions.get_camel_space(camel)
            if space and space >= FINISH_LINE:
                self.log(f"{_CAMEL_FULL_NAMES[camel]} camel crosses finish line at space {space}!")
                break

        self.log(f"Final ranking: {render_ranking(state.board)}")

        # Overall bet scoring
        self.log("Overall scoring:")
        winner = ranking[0] if ranking else None
        loser = ranking[-1] if ranking else None

        for i in range(len(state.players)):
            parts = []
            # Winner bets
            for bet in state.betting.winner_bets:
                if bet.player == i:
                    if bet.camel == winner:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[bet.camel]} wins -> correct")
                    else:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[bet.camel]} wins -> wrong (-1)")
            # Loser bets
            for bet in state.betting.loser_bets:
                if bet.player == i:
                    if bet.camel == loser:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[bet.camel]} loses -> correct")
                    else:
                        parts.append(f"Bet {_CAMEL_FULL_NAMES[bet.camel]} loses -> wrong (-1)")

            if parts:
                self.log(f"  P{i}: {'; '.join(parts)}")
            else:
                self.log(f"  P{i}: no overall bets")

        self.log(render_scores(state.players))

        # Winner
        winner_idx = state.get_winner()
        if winner_idx is not None:
            agent_name = ""  # Agent name not available here, handled in play_game
            self.log(f"Winner: Player {winner_idx}")
        else:
            self.log("Result: Tie")

        self.close()


def _action_short(action):
    """Short description of an action for EV display."""
    if action.action_type == ActionType.TAKE_BETTING_TICKET:
        return f"Bet{action.camel.value.capitalize()}"
    elif action.action_type == ActionType.TAKE_PYRAMID_TICKET:
        return "Roll"
    elif action.action_type == ActionType.PLACE_SPECTATOR_TILE:
        side = "Ch" if action.is_cheering else "Bo"
        return f"Tile{side}{action.space}"
    elif action.action_type == ActionType.BET_OVERALL_WINNER:
        return f"Win{action.camel.value.capitalize()}"
    elif action.action_type == ActionType.BET_OVERALL_LOSER:
        return f"Los{action.camel.value.capitalize()}"
    return str(action.action_type)
