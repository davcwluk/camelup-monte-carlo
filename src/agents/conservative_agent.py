"""Conservative agent that prefers low-risk actions."""

from typing import List, Dict, Tuple

from .base import Agent
from ..game.game import GameState, Action, ActionType
from ..game.camel import CamelColor, RACING_CAMELS
from ..game.dice import DieColor
from ..probability.calculator import calculate_all_probabilities
from ..probability.ev import calculate_leg_ticket_ev


# Minimum probability to place a leg bet
MIN_BET_PROBABILITY = 0.5

# Minimum probability to place an overall bet
MIN_OVERALL_PROBABILITY = 0.6

# Minimum probability that game ends this leg to consider overall bets
MIN_GAME_END_PROBABILITY = 0.4


class ConservativeAgent(Agent):
    """
    Risk-averse agent that prefers guaranteed returns.

    Strategy:
    - Only bets on leg winners when probability > 50%
    - Prefers pyramid tickets for guaranteed +1
    - Avoids overall winner/loser bets unless very confident
    - Never places spectator tiles (uncertain return)

    Purpose: Test whether low-variance strategy is viable.
    """

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        min_bet_prob: float = MIN_BET_PROBABILITY,
        min_overall_prob: float = MIN_OVERALL_PROBABILITY,
        min_game_end_prob: float = MIN_GAME_END_PROBABILITY,
        fast_mode: bool = False
    ):
        """
        Initialize the conservative agent.

        Args:
            name: Optional name for the agent
            seed: Random seed for reproducibility
            min_bet_prob: Minimum P(1st or 2nd) to place leg bet
            min_overall_prob: Minimum P(wins/loses) to place overall bet
            min_game_end_prob: Minimum P(game ends) to consider overall bets
            fast_mode: If True, skip grey die in probability calculations
        """
        super().__init__(name, seed)
        self.min_bet_prob = min_bet_prob
        self.min_overall_prob = min_overall_prob
        self.min_game_end_prob = min_game_end_prob
        self.fast_mode = fast_mode

    def choose_action(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """Choose action with conservative strategy."""
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

        # Priority 1: High-confidence leg bets (>50% chance of top 2)
        best_leg_bet = self._find_best_leg_bet(
            legal_actions, full_probs.ranking, available_tickets
        )
        if best_leg_bet:
            return best_leg_bet

        # Priority 2: Pyramid ticket (guaranteed +1)
        pyramid_action = self._find_pyramid_action(legal_actions)
        if pyramid_action:
            return pyramid_action

        # Priority 3: High-confidence overall bets (very late game only)
        if full_probs.overall_race.prob_game_ends >= self.min_game_end_prob:
            overall_bet = self._find_best_overall_bet(
                legal_actions, full_probs.overall_race, state
            )
            if overall_bet:
                return overall_bet

        # Priority 4: Any available leg bet (even lower probability)
        any_leg_bet = self._find_any_leg_bet(legal_actions)
        if any_leg_bet:
            return any_leg_bet

        # Fallback: Random from remaining actions
        return self.rng.choice(legal_actions)

    def _get_available_tickets(
        self,
        state: GameState
    ) -> Dict[CamelColor, Tuple[int, ...]]:
        """Get available ticket values for each camel."""
        return state.betting.available_tickets

    def _find_best_leg_bet(
        self,
        legal_actions: List[Action],
        ranking_probs,
        available_tickets: Dict[CamelColor, Tuple[int, ...]]
    ) -> Action | None:
        """Find a high-confidence leg bet."""
        leg_bets = [
            a for a in legal_actions
            if a.action_type == ActionType.TAKE_BETTING_TICKET
        ]

        best_action = None
        best_ev = 0.0

        for action in leg_bets:
            prob_top_two = ranking_probs.prob_top_two(action.camel)

            if prob_top_two >= self.min_bet_prob:
                tickets = available_tickets.get(action.camel, ())
                if tickets:
                    top_value = tickets[0]
                    ev = calculate_leg_ticket_ev(
                        ranking_probs, action.camel, top_value
                    )
                    if ev > best_ev:
                        best_ev = ev
                        best_action = action

        return best_action

    def _find_pyramid_action(
        self,
        legal_actions: List[Action]
    ) -> Action | None:
        """Find pyramid ticket action if available."""
        for action in legal_actions:
            if action.action_type == ActionType.TAKE_PYRAMID_TICKET:
                return action
        return None

    def _find_best_overall_bet(
        self,
        legal_actions: List[Action],
        overall_probs,
        state: GameState
    ) -> Action | None:
        """Find a high-confidence overall bet."""
        # Winner bets
        for action in legal_actions:
            if action.action_type == ActionType.BET_OVERALL_WINNER:
                prob_wins = overall_probs.prob_wins_race(action.camel)
                if prob_wins >= self.min_overall_prob:
                    return action

        # Loser bets
        for action in legal_actions:
            if action.action_type == ActionType.BET_OVERALL_LOSER:
                prob_loses = overall_probs.prob_loses_race(action.camel)
                if prob_loses >= self.min_overall_prob:
                    return action

        return None

    def _find_any_leg_bet(
        self,
        legal_actions: List[Action]
    ) -> Action | None:
        """Find any leg bet action."""
        leg_bets = [
            a for a in legal_actions
            if a.action_type == ActionType.TAKE_BETTING_TICKET
        ]
        if leg_bets:
            return self.rng.choice(leg_bets)
        return None
