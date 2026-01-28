"""Expected Value calculations for Camel Up betting decisions.

Provides EV calculations for all possible actions given the current
probability distribution of outcomes.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..game.camel import CamelColor, RACING_CAMELS
from ..game.betting import TICKET_VALUES, OVERALL_PAYOUTS
from .calculator import RankingProbabilities


@dataclass(frozen=True)
class ActionEV:
    """Expected value for a single action."""
    action_description: str
    expected_value: float
    
    def __str__(self) -> str:
        return f"{self.action_description}: EV = {self.expected_value:+.3f}"


@dataclass(frozen=True)
class BettingEVs:
    """Expected values for all betting actions."""
    leg_ticket_evs: Dict[CamelColor, float]  # EV for taking each camel's top ticket
    pyramid_ticket_ev: float  # Always +1
    
    def best_leg_bet(self) -> Tuple[CamelColor, float]:
        """Return the best leg bet and its EV."""
        best_camel = max(self.leg_ticket_evs, key=self.leg_ticket_evs.get)
        return best_camel, self.leg_ticket_evs[best_camel]
    
    def should_take_pyramid(self) -> bool:
        """Whether pyramid ticket (+1) is better than best leg bet."""
        _, best_ev = self.best_leg_bet()
        return self.pyramid_ticket_ev > best_ev


def calculate_leg_ticket_ev(
    probs: RankingProbabilities,
    camel: CamelColor,
    ticket_value: int
) -> float:
    """
    Calculate expected value of taking a leg betting ticket.
    
    Payouts:
    - Camel finishes 1st: +ticket_value
    - Camel finishes 2nd: +1
    - Camel finishes 3rd-5th: -1
    
    Args:
        probs: Current ranking probabilities
        camel: Camel to bet on
        ticket_value: Value of the ticket (5, 3, or 2)
    
    Returns:
        Expected value in coins
    """
    p_first = probs.prob_first(camel)
    p_second = probs.prob_second(camel)
    p_other = 1.0 - p_first - p_second
    
    ev = (p_first * ticket_value) + (p_second * 1) + (p_other * -1)
    return ev


def calculate_all_leg_ticket_evs(
    probs: RankingProbabilities,
    available_tickets: Dict[CamelColor, Tuple[int, ...]]
) -> Dict[CamelColor, float]:
    """
    Calculate EV for all available leg betting tickets.
    
    Args:
        probs: Current ranking probabilities
        available_tickets: Map of camel -> available ticket values
    
    Returns:
        Map of camel -> EV for taking their top ticket
    """
    evs = {}
    for camel in RACING_CAMELS:
        tickets = available_tickets.get(camel, ())
        if tickets:
            top_ticket_value = tickets[0]  # Top ticket has highest value
            evs[camel] = calculate_leg_ticket_ev(probs, camel, top_ticket_value)
    return evs


def calculate_pyramid_ticket_ev() -> float:
    """
    Expected value of taking a pyramid ticket.
    
    Always returns +1 coin (guaranteed).
    """
    return 1.0


def calculate_overall_bet_ev(
    prob_correct: float,
    position_in_queue: int
) -> float:
    """
    Calculate EV for an overall winner/loser bet.
    
    Args:
        prob_correct: Probability the bet is correct
        position_in_queue: How many correct bets are already placed (0 = first)
    
    Returns:
        Expected value
    
    Payouts for correct: 8, 5, 3, 2, 1, 1, 1, 1 (by position)
    Payout for incorrect: -1
    """
    if position_in_queue >= len(OVERALL_PAYOUTS):
        payout_if_correct = 1  # Beyond the list, assume +1
    else:
        payout_if_correct = OVERALL_PAYOUTS[position_in_queue]
    
    ev = (prob_correct * payout_if_correct) + ((1 - prob_correct) * -1)
    return ev


def calculate_betting_evs(
    probs: RankingProbabilities,
    available_tickets: Dict[CamelColor, Tuple[int, ...]]
) -> BettingEVs:
    """
    Calculate EVs for all betting actions.
    
    Args:
        probs: Current ranking probabilities
        available_tickets: Available leg betting tickets
    
    Returns:
        BettingEVs with all calculated values
    """
    leg_evs = calculate_all_leg_ticket_evs(probs, available_tickets)
    pyramid_ev = calculate_pyramid_ticket_ev()
    
    return BettingEVs(
        leg_ticket_evs=leg_evs,
        pyramid_ticket_ev=pyramid_ev
    )


def rank_actions_by_ev(
    probs: RankingProbabilities,
    available_tickets: Dict[CamelColor, Tuple[int, ...]]
) -> List[ActionEV]:
    """
    Rank all available betting actions by expected value.
    
    Args:
        probs: Current ranking probabilities
        available_tickets: Available leg betting tickets
    
    Returns:
        List of ActionEV sorted by EV (highest first)
    """
    actions = []
    
    # Leg betting tickets
    for camel in RACING_CAMELS:
        tickets = available_tickets.get(camel, ())
        if tickets:
            top_value = tickets[0]
            ev = calculate_leg_ticket_ev(probs, camel, top_value)
            actions.append(ActionEV(
                action_description=f"Bet on {camel.value} (ticket value {top_value})",
                expected_value=ev
            ))
    
    # Pyramid ticket
    actions.append(ActionEV(
        action_description="Take pyramid ticket",
        expected_value=1.0
    ))
    
    # Sort by EV descending
    actions.sort(key=lambda a: a.expected_value, reverse=True)
    return actions


def format_probabilities(probs: RankingProbabilities) -> str:
    """Format probabilities as a readable string."""
    lines = ["Camel Ranking Probabilities:"]
    lines.append("-" * 50)
    lines.append(f"{'Camel':<10} {'1st':>8} {'2nd':>8} {'Top 2':>8}")
    lines.append("-" * 50)
    
    # Sort camels by 1st place probability
    sorted_camels = sorted(
        RACING_CAMELS,
        key=lambda c: probs.prob_first(c),
        reverse=True
    )
    
    for camel in sorted_camels:
        p1 = probs.prob_first(camel) * 100
        p2 = probs.prob_second(camel) * 100
        p_top2 = probs.prob_top_two(camel) * 100
        lines.append(f"{camel.value:<10} {p1:>7.1f}% {p2:>7.1f}% {p_top2:>7.1f}%")
    
    return "\n".join(lines)


def format_evs(
    probs: RankingProbabilities,
    available_tickets: Dict[CamelColor, Tuple[int, ...]]
) -> str:
    """Format EV analysis as a readable string."""
    actions = rank_actions_by_ev(probs, available_tickets)
    
    lines = ["Action Expected Values (sorted by EV):"]
    lines.append("-" * 50)
    
    for action in actions:
        lines.append(f"  {action}")
    
    return "\n".join(lines)
