"""Main game orchestration for Camel Up."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple
import random

from .camel import (
    CamelColor, CamelPositions, RACING_CAMELS, CRAZY_CAMELS,
    create_initial_positions
)
from .board import Board, TRACK_LENGTH, FINISH_LINE, CRAZY_START_POSITIONS
from .dice import Pyramid, DieColor, roll_racing_die, roll_grey_die, DieRoll
from .betting import (
    BettingState, BettingTicket, PlayerState,
    calculate_leg_scores, calculate_overall_scores
)
from .spectator import get_tile_payout


class ActionType(Enum):
    """Types of actions a player can take."""
    TAKE_BETTING_TICKET = auto()  # Take a leg betting ticket
    PLACE_SPECTATOR_TILE = auto()  # Place/move spectator tile
    TAKE_PYRAMID_TICKET = auto()  # Roll dice and take pyramid ticket
    BET_OVERALL_WINNER = auto()  # Bet on overall winner
    BET_OVERALL_LOSER = auto()  # Bet on overall loser


@dataclass(frozen=True)
class Action:
    """An action a player can take."""
    action_type: ActionType
    # For betting ticket: which camel to bet on
    camel: CamelColor | None = None
    # For spectator tile: which space and which side (True=cheering)
    space: int | None = None
    is_cheering: bool | None = None

    def __str__(self) -> str:
        if self.action_type == ActionType.TAKE_BETTING_TICKET:
            return f"Bet on {self.camel.value} for leg"
        elif self.action_type == ActionType.PLACE_SPECTATOR_TILE:
            side = "cheering" if self.is_cheering else "booing"
            return f"Place {side} tile on space {self.space}"
        elif self.action_type == ActionType.TAKE_PYRAMID_TICKET:
            return "Roll dice (take pyramid ticket)"
        elif self.action_type == ActionType.BET_OVERALL_WINNER:
            return f"Bet {self.camel.value} wins overall"
        elif self.action_type == ActionType.BET_OVERALL_LOSER:
            return f"Bet {self.camel.value} loses overall"
        return str(self.action_type)


@dataclass(frozen=True)
class GameState:
    """Complete game state."""
    board: Board
    pyramid: Pyramid
    betting: BettingState
    players: Tuple[PlayerState, ...]
    current_player: int
    leg_number: int = 1
    is_game_over: bool = False
    # Random state for reproducibility
    rng_state: tuple | None = None
    # Track last player to take pyramid ticket (for starting player rule)
    last_pyramid_ticket_player: int | None = None

    @classmethod
    def create_new_game(
        cls,
        num_players: int,
        seed: int | None = None
    ) -> "GameState":
        """Create a new game with initial setup."""
        rng = random.Random(seed)

        # Roll for initial racing camel positions
        camel_rolls = []
        for camel in RACING_CAMELS:
            die_color = DieColor[camel.name]
            roll = roll_racing_die(die_color, rng)
            camel_rolls.append((camel, roll.value))

        # Roll for crazy camel positions
        grey_roll_1 = roll_grey_die(rng)
        grey_roll_2 = roll_grey_die(rng)

        crazy_positions = [
            (CamelColor.WHITE, CRAZY_START_POSITIONS[grey_roll_1.value]),
            (CamelColor.BLACK, CRAZY_START_POSITIONS[grey_roll_2.value]),
        ]

        # Create initial positions
        positions = create_initial_positions(camel_rolls, crazy_positions)

        # Create board
        board = Board(camel_positions=positions, spectator_tiles={})

        # Create player states
        players = tuple(PlayerState() for _ in range(num_players))

        # Create betting state
        betting = BettingState.create_for_players(num_players)

        # Create pyramid
        pyramid = Pyramid()

        return cls(
            board=board,
            pyramid=pyramid,
            betting=betting,
            players=players,
            current_player=0,
            leg_number=1,
            is_game_over=False,
            rng_state=rng.getstate()
        )

    def get_num_players(self) -> int:
        """Get the number of players."""
        return len(self.players)

    def get_current_player_state(self) -> PlayerState:
        """Get the current player's state."""
        return self.players[self.current_player]

    def get_legal_actions(self) -> List[Action]:
        """Get all legal actions for the current player."""
        if self.is_game_over:
            return []

        actions = []
        player_state = self.get_current_player_state()

        # Action 1: Take betting ticket
        for ticket in self.betting.get_all_available_tickets():
            actions.append(Action(
                action_type=ActionType.TAKE_BETTING_TICKET,
                camel=ticket.camel
            ))

        # Action 2: Place spectator tile (if available)
        if player_state.has_spectator_tile:
            valid_spaces = self.board.get_valid_spectator_spaces(self.current_player)
            for space in valid_spaces:
                # Can place either side
                actions.append(Action(
                    action_type=ActionType.PLACE_SPECTATOR_TILE,
                    space=space,
                    is_cheering=True
                ))
                actions.append(Action(
                    action_type=ActionType.PLACE_SPECTATOR_TILE,
                    space=space,
                    is_cheering=False
                ))

        # Action 3: Take pyramid ticket (roll dice)
        if not self.pyramid.is_leg_complete():
            actions.append(Action(action_type=ActionType.TAKE_PYRAMID_TICKET))

        # Action 4: Bet on overall winner/loser
        for camel in RACING_CAMELS:
            if player_state.can_bet_on_overall(camel):
                actions.append(Action(
                    action_type=ActionType.BET_OVERALL_WINNER,
                    camel=camel
                ))
                actions.append(Action(
                    action_type=ActionType.BET_OVERALL_LOSER,
                    camel=camel
                ))

        return actions

    def apply_action(
        self,
        action: Action,
        rng: random.Random | None = None
    ) -> "GameState":
        """
        Apply an action and return the new game state.

        Note: This may trigger leg end or game end processing.
        """
        if self.is_game_over:
            raise ValueError("Game is already over")

        if rng is None:
            rng = random.Random()
            if self.rng_state:
                rng.setstate(self.rng_state)

        new_board = self.board
        new_pyramid = self.pyramid
        new_betting = self.betting
        new_players = list(self.players)
        spectator_owner = None
        die_roll = None
        new_last_pyramid_player = self.last_pyramid_ticket_player

        player = self.current_player
        player_state = self.players[player]

        if action.action_type == ActionType.TAKE_BETTING_TICKET:
            # Take a betting ticket
            new_betting = self.betting.take_ticket(player, action.camel)

        elif action.action_type == ActionType.PLACE_SPECTATOR_TILE:
            # Place spectator tile
            new_board = self.board.place_spectator_tile(
                action.space, player, action.is_cheering
            )
            new_players[player] = player_state.use_spectator_tile()

        elif action.action_type == ActionType.TAKE_PYRAMID_TICKET:
            # Take pyramid ticket and roll dice
            new_betting = self.betting.take_pyramid_ticket(player)
            new_last_pyramid_player = player  # Track for starting player rule
            new_pyramid, die_roll = self.pyramid.roll_from_pyramid(rng)

            # Move the appropriate camel
            if die_roll.color == DieColor.GREY:
                # Grey die - determine which crazy camel to move
                grey_die_camel = (CamelColor.WHITE if die_roll.crazy_camel == "white"
                                  else CamelColor.BLACK)

                # Apply crazy camel priority/stack rules
                camel = new_board.camel_positions.get_crazy_camel_to_move(grey_die_camel)

                # Crazy camels move backwards (negative)
                new_board, spectator_owner = new_board.move_camel(
                    camel, -die_roll.value
                )
            else:
                # Racing die - move racing camel
                camel = CamelColor[die_roll.color.name]
                new_board, spectator_owner = new_board.move_camel(
                    camel, die_roll.value
                )

            # Pay spectator tile owner
            if spectator_owner is not None:
                new_players[spectator_owner] = new_players[spectator_owner].add_coins(
                    get_tile_payout()
                )

        elif action.action_type == ActionType.BET_OVERALL_WINNER:
            # Bet on overall winner
            new_betting = self.betting.place_overall_bet(
                player, action.camel, is_winner_bet=True
            )
            new_players[player] = player_state.use_finish_card(action.camel)

        elif action.action_type == ActionType.BET_OVERALL_LOSER:
            # Bet on overall loser
            new_betting = self.betting.place_overall_bet(
                player, action.camel, is_winner_bet=False
            )
            new_players[player] = player_state.use_finish_card(action.camel)

        # Check for game end
        is_game_over = new_board.is_game_over()

        # Check for leg end
        leg_ended = new_pyramid.is_leg_complete() and not is_game_over

        # Process leg end
        new_leg_number = self.leg_number
        if leg_ended or is_game_over:
            # Calculate leg scores
            ranking = new_board.get_ranking()
            first = ranking[0] if ranking else None
            second = ranking[1] if len(ranking) > 1 else None

            if first and second:
                leg_scores = calculate_leg_scores(new_betting, first, second)
                for i, score in enumerate(leg_scores):
                    new_players[i] = new_players[i].add_coins(score)

            if not is_game_over:
                # Reset for new leg
                new_pyramid = Pyramid()
                new_betting = new_betting.reset_for_new_leg()
                new_board = new_board.clear_all_spectator_tiles()

                # Return spectator tiles to players
                for i in range(len(new_players)):
                    new_players[i] = new_players[i].return_spectator_tile()

                new_leg_number += 1

        # Process game end
        if is_game_over:
            ranking = new_board.get_ranking()
            winner = ranking[0] if ranking else None
            loser = ranking[-1] if ranking else None

            if winner and loser:
                overall_scores = calculate_overall_scores(new_betting, winner, loser)
                for i, score in enumerate(overall_scores):
                    new_players[i] = new_players[i].add_coins(score)

        # Advance to next player
        # Starting player rule: if leg just ended, start with player to the left
        # of the last pyramid ticket taker
        if leg_ended and new_last_pyramid_player is not None:
            # Player to the left = next player after last pyramid ticket taker
            next_player = (new_last_pyramid_player + 1) % len(new_players)
            # Reset the tracker for the new leg
            new_last_pyramid_player = None
        else:
            next_player = (player + 1) % len(new_players)

        return GameState(
            board=new_board,
            pyramid=new_pyramid,
            betting=new_betting,
            players=tuple(new_players),
            current_player=next_player,
            leg_number=new_leg_number,
            is_game_over=is_game_over,
            rng_state=rng.getstate(),
            last_pyramid_ticket_player=new_last_pyramid_player
        )

    def get_scores(self) -> Tuple[int, ...]:
        """Get current scores (coins) for all players."""
        return tuple(p.coins for p in self.players)

    def get_winner(self) -> int | None:
        """Get the winning player index, or None if tied/not over."""
        if not self.is_game_over:
            return None

        scores = self.get_scores()
        max_score = max(scores)

        # Check for tie
        if scores.count(max_score) > 1:
            return None  # Tie

        return scores.index(max_score)

    def __str__(self) -> str:
        """String representation for debugging."""
        lines = [
            f"=== Camel Up - Leg {self.leg_number} ===",
            f"Current player: {self.current_player}",
            f"Scores: {self.get_scores()}",
            "",
            "Board:",
            str(self.board),
            "",
            f"Dice in pyramid: {[d.value for d in self.pyramid.remaining]}",
            f"Grey die available: {not self.pyramid.grey_rolled}",
        ]
        return "\n".join(lines)


def play_game(
    num_players: int,
    agent_functions: List,
    seed: int | None = None,
    verbose: bool = False
) -> Tuple[GameState, List[Action]]:
    """
    Play a complete game with given agent functions.

    Args:
        num_players: Number of players
        agent_functions: List of functions that take (state, legal_actions) and return action
        seed: Random seed for reproducibility
        verbose: Print game state after each action

    Returns:
        Tuple of (final_state, action_history)
    """
    state = GameState.create_new_game(num_players, seed)
    rng = random.Random(seed)
    history = []

    while not state.is_game_over:
        legal_actions = state.get_legal_actions()

        if not legal_actions:
            break  # No legal actions (shouldn't happen normally)

        # Get agent's action
        agent = agent_functions[state.current_player]
        action = agent(state, legal_actions)

        if action not in legal_actions:
            raise ValueError(f"Agent returned illegal action: {action}")

        history.append(action)

        if verbose:
            print(f"Player {state.current_player}: {action}")

        state = state.apply_action(action, rng)

        if verbose:
            print(state)
            print()

    return state, history
