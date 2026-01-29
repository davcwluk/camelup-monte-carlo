"""Heuristic agent with human-like decision rules."""

from typing import List, Dict, Tuple

from .base import Agent
from ..game.game import GameState, Action, ActionType
from ..game.camel import CamelColor, RACING_CAMELS
from ..game.dice import DieColor
from ..probability.calculator import calculate_all_probabilities


# Probability threshold to bet on a camel
LEADER_THRESHOLD = 0.4

# How many dice must remain to consider spectator tile
MIN_DICE_FOR_SPECTATOR = 4


class HeuristicAgent(Agent):
    """
    Rule-based agent that approximates casual human play.

    Strategy:
    1. If leader has > 40% win probability, take their betting ticket
    2. If early in leg (4+ dice remaining), consider spectator tile
    3. If all good tickets are taken, roll dice (pyramid ticket)
    4. Avoid overall bets until very late game

    Purpose: Approximate how a casual human player might play.
    """

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        leader_threshold: float = LEADER_THRESHOLD,
        min_dice_for_spectator: int = MIN_DICE_FOR_SPECTATOR,
        fast_mode: bool = False
    ):
        """
        Initialize the heuristic agent.

        Args:
            name: Optional name for the agent
            seed: Random seed for reproducibility
            leader_threshold: Min P(1st) to bet on a camel
            min_dice_for_spectator: Dice remaining to place spectator tile
            fast_mode: If True, skip grey die in probability calculations
        """
        super().__init__(name, seed)
        self.leader_threshold = leader_threshold
        self.min_dice_for_spectator = min_dice_for_spectator
        self.fast_mode = fast_mode

    def choose_action(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """Choose action using human-like heuristics."""
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

        # Count remaining dice
        num_remaining = len(remaining_racing) + (1 if grey_available else 0)

        # Rule 1: Bet on leader if probability is high enough
        leader_bet = self._find_leader_bet(legal_actions, full_probs.ranking)
        if leader_bet:
            return leader_bet

        # Rule 2: Place spectator tile early in leg if good space available
        if num_remaining >= self.min_dice_for_spectator:
            spectator_action = self._find_good_spectator_placement(
                legal_actions, full_probs.space_landings
            )
            if spectator_action:
                return spectator_action

        # Rule 3: If can't find good bet, roll dice
        pyramid_action = self._find_pyramid_action(legal_actions)
        if pyramid_action:
            return pyramid_action

        # Rule 4: Late game - consider overall bets
        if full_probs.overall_race.prob_game_ends > 0.5:
            overall_bet = self._find_obvious_overall_bet(
                legal_actions, full_probs.overall_race
            )
            if overall_bet:
                return overall_bet

        # Fallback: Random action
        return self.rng.choice(legal_actions)

    def _find_leader_bet(
        self,
        legal_actions: List[Action],
        ranking_probs
    ) -> Action | None:
        """Find a bet on the likely leader."""
        leg_bets = [
            a for a in legal_actions
            if a.action_type == ActionType.TAKE_BETTING_TICKET
        ]

        # Find camel with highest P(1st)
        best_camel = None
        best_prob = 0.0

        for camel in RACING_CAMELS:
            p_first = ranking_probs.prob_first(camel)
            if p_first > best_prob:
                best_prob = p_first
                best_camel = camel

        # Bet if probability exceeds threshold
        if best_prob >= self.leader_threshold and best_camel:
            for action in leg_bets:
                if action.camel == best_camel:
                    return action

        return None

    def _find_good_spectator_placement(
        self,
        legal_actions: List[Action],
        space_probs
    ) -> Action | None:
        """Find a good spectator tile placement."""
        spectator_actions = [
            a for a in legal_actions
            if a.action_type == ActionType.PLACE_SPECTATOR_TILE
        ]

        if not spectator_actions:
            return None

        # Find space with highest landing probability
        best_action = None
        best_prob = 0.0

        for action in spectator_actions:
            prob = space_probs.prob_landing(action.space)
            if prob > best_prob:
                best_prob = prob
                best_action = action

        # Only place if there's a reasonable chance of landing
        # (at least 20% chance)
        if best_prob >= 0.2:
            return best_action

        return None

    def _find_pyramid_action(
        self,
        legal_actions: List[Action]
    ) -> Action | None:
        """Find pyramid ticket action if available."""
        for action in legal_actions:
            if action.action_type == ActionType.TAKE_PYRAMID_TICKET:
                return action
        return None

    def _find_obvious_overall_bet(
        self,
        legal_actions: List[Action],
        overall_probs
    ) -> Action | None:
        """Find an obvious overall bet (very high probability)."""
        # Look for a camel very likely to win
        for action in legal_actions:
            if action.action_type == ActionType.BET_OVERALL_WINNER:
                if overall_probs.prob_wins_race(action.camel) > 0.7:
                    return action

        # Look for a camel very likely to lose
        for action in legal_actions:
            if action.action_type == ActionType.BET_OVERALL_LOSER:
                if overall_probs.prob_loses_race(action.camel) > 0.7:
                    return action

        return None
