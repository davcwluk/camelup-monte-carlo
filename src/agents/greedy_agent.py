"""Greedy agent that picks the highest immediate EV action."""

from typing import List, Dict, Tuple

from .base import Agent
from ..game.game import GameState, Action, ActionType
from ..game.camel import CamelColor, RACING_CAMELS
from ..game.dice import DieColor
from ..probability.calculator import calculate_all_probabilities
from ..probability.ev import (
    calculate_leg_ticket_ev,
    calculate_spectator_tile_ev,
    calculate_overall_winner_bet_ev,
    calculate_overall_loser_bet_ev,
)


# Threshold for considering overall bets
# Only bet on overall winner/loser when probability of game ending is above this
OVERALL_BET_THRESHOLD = 0.3


class GreedyAgent(Agent):
    """
    Agent that always picks the highest immediate expected value action.

    Uses exact probability enumeration to calculate EV for each action
    and picks the maximum. Does not consider future turns.

    Overall bets are only considered when the game is likely to end
    this leg (prob_game_ends > OVERALL_BET_THRESHOLD).

    Purpose: Simple EV-based strategy to test whether probability
    calculations provide an advantage.
    """

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        overall_bet_threshold: float = OVERALL_BET_THRESHOLD,
        fast_mode: bool = False
    ):
        """
        Initialize the greedy agent.

        Args:
            name: Optional name for the agent
            seed: Random seed for reproducibility
            overall_bet_threshold: Only consider overall bets when
                prob_game_ends exceeds this threshold (default 0.3)
            fast_mode: If True, skip grey die in probability calculations
                (faster but less accurate). Use for testing.
        """
        super().__init__(name, seed)
        self.overall_bet_threshold = overall_bet_threshold
        self.fast_mode = fast_mode

    def choose_action(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """Choose the action with highest expected value."""
        # Get remaining dice info
        remaining_racing = [
            DieColor[c.name] for c in RACING_CAMELS
            if DieColor[c.name] in state.pyramid.remaining
        ]
        # In fast_mode, skip grey die for faster calculation
        grey_available = not state.pyramid.grey_rolled and not self.fast_mode

        # Calculate probabilities
        full_probs = calculate_all_probabilities(
            state.board,
            remaining_racing,
            grey_available
        )

        # Get available ticket values
        available_tickets = self._get_available_tickets(state)

        # Calculate EV for each legal action
        action_evs: List[Tuple[Action, float]] = []

        for action in legal_actions:
            ev = self._calculate_action_ev(
                action, state, full_probs, available_tickets
            )
            action_evs.append((action, ev))

        # Sort by EV descending and pick the best
        action_evs.sort(key=lambda x: x[1], reverse=True)

        # If multiple actions have the same EV, pick randomly among them
        best_ev = action_evs[0][1]
        best_actions = [a for a, ev in action_evs if ev == best_ev]

        return self.rng.choice(best_actions)

    def _get_available_tickets(
        self,
        state: GameState
    ) -> Dict[CamelColor, Tuple[int, ...]]:
        """Get available ticket values for each camel."""
        return state.betting.available_tickets

    def _calculate_action_ev(
        self,
        action: Action,
        state: GameState,
        full_probs,
        available_tickets: Dict[CamelColor, Tuple[int, ...]]
    ) -> float:
        """Calculate expected value for a single action."""

        if action.action_type == ActionType.TAKE_BETTING_TICKET:
            # Leg betting ticket
            tickets = available_tickets.get(action.camel, ())
            if tickets:
                top_value = tickets[0]
                return calculate_leg_ticket_ev(
                    full_probs.ranking, action.camel, top_value
                )
            return -1.0  # Fallback (shouldn't happen)

        elif action.action_type == ActionType.TAKE_PYRAMID_TICKET:
            # Pyramid ticket is guaranteed +1
            return 1.0

        elif action.action_type == ActionType.PLACE_SPECTATOR_TILE:
            # Spectator tile EV based on landing probability
            return calculate_spectator_tile_ev(
                full_probs.space_landings, action.space
            )

        elif action.action_type == ActionType.BET_OVERALL_WINNER:
            # Only consider if game likely to end soon
            if full_probs.overall_race.prob_game_ends < self.overall_bet_threshold:
                return -2.0  # Discourage early overall bets

            # Count existing winner bets to determine position in queue
            num_winner_bets = len(state.betting.winner_bets)
            return calculate_overall_winner_bet_ev(
                full_probs.overall_race, action.camel, num_winner_bets
            )

        elif action.action_type == ActionType.BET_OVERALL_LOSER:
            # Only consider if game likely to end soon
            if full_probs.overall_race.prob_game_ends < self.overall_bet_threshold:
                return -2.0  # Discourage early overall bets

            # Count existing loser bets to determine position in queue
            num_loser_bets = len(state.betting.loser_bets)
            return calculate_overall_loser_bet_ev(
                full_probs.overall_race, action.camel, num_loser_bets
            )

        return 0.0  # Unknown action type
