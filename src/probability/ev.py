"""Expected Value calculations for Camel Up betting decisions.

Provides EV calculations for all possible actions given the current
probability distribution of outcomes.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..game.camel import CamelColor, RACING_CAMELS
from ..game.betting import TICKET_VALUES, OVERALL_PAYOUTS
from .calculator import (
    RankingProbabilities, SpaceLandingProbabilities,
    OverallRaceProbabilities, FullProbabilities
)


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


def calculate_spectator_tile_ev(
    space_probs: SpaceLandingProbabilities,
    space: int
) -> float:
    """
    Calculate EV for placing a spectator tile on a space.

    Payout: 1 coin each time any camel lands on the space.

    Args:
        space_probs: Probability distribution for space landings
        space: The space to place the tile on

    Returns:
        Expected value (expected number of coins from landings)
    """
    return space_probs.prob_landing(space) * 1.0


def calculate_all_spectator_tile_evs(
    space_probs: SpaceLandingProbabilities,
    valid_spaces: List[int]
) -> Dict[int, float]:
    """
    Calculate EV for all valid spectator tile placements.

    Args:
        space_probs: Probability distribution for space landings
        valid_spaces: List of spaces where tile can be placed

    Returns:
        Map of space -> EV
    """
    return {
        space: calculate_spectator_tile_ev(space_probs, space)
        for space in valid_spaces
    }


def calculate_overall_winner_bet_ev(
    overall_probs: OverallRaceProbabilities,
    camel: CamelColor,
    position_in_queue: int
) -> float:
    """
    Calculate EV for betting on a camel to win the race.

    Args:
        overall_probs: Probability distribution for race outcomes
        camel: Camel to bet on
        position_in_queue: How many winner bets are already placed (0 = first)

    Returns:
        Expected value
    """
    prob_wins = overall_probs.prob_wins_race(camel)
    return calculate_overall_bet_ev(prob_wins, position_in_queue)


def calculate_overall_loser_bet_ev(
    overall_probs: OverallRaceProbabilities,
    camel: CamelColor,
    position_in_queue: int
) -> float:
    """
    Calculate EV for betting on a camel to lose the race.

    Args:
        overall_probs: Probability distribution for race outcomes
        camel: Camel to bet on
        position_in_queue: How many loser bets are already placed (0 = first)

    Returns:
        Expected value
    """
    prob_loses = overall_probs.prob_loses_race(camel)
    return calculate_overall_bet_ev(prob_loses, position_in_queue)


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


def rank_all_actions_by_ev(
    full_probs: FullProbabilities,
    available_tickets: Dict[CamelColor, Tuple[int, ...]],
    valid_spectator_spaces: List[int],
    available_finish_cards: List[CamelColor],
    num_winner_bets_placed: int = 0,
    num_loser_bets_placed: int = 0
) -> List[ActionEV]:
    """
    Rank ALL available actions by expected value.

    Includes leg bets, pyramid ticket, spectator tiles, and overall bets.

    Args:
        full_probs: Complete probability analysis
        available_tickets: Available leg betting tickets
        valid_spectator_spaces: Spaces where spectator tile can be placed
        available_finish_cards: Camels player can still bet on for overall
        num_winner_bets_placed: How many winner bets already in queue
        num_loser_bets_placed: How many loser bets already in queue

    Returns:
        List of ActionEV sorted by EV (highest first)
    """
    actions = []

    # Leg betting tickets
    for camel in RACING_CAMELS:
        tickets = available_tickets.get(camel, ())
        if tickets:
            top_value = tickets[0]
            ev = calculate_leg_ticket_ev(full_probs.ranking, camel, top_value)
            actions.append(ActionEV(
                action_description=f"Leg bet: {camel.value} (value {top_value})",
                expected_value=ev
            ))

    # Pyramid ticket
    actions.append(ActionEV(
        action_description="Pyramid ticket (+1 coin)",
        expected_value=1.0
    ))

    # Spectator tiles
    for space in valid_spectator_spaces:
        ev = calculate_spectator_tile_ev(full_probs.space_landings, space)
        actions.append(ActionEV(
            action_description=f"Spectator tile: space {space}",
            expected_value=ev
        ))

    # Overall winner bets
    for camel in available_finish_cards:
        ev = calculate_overall_winner_bet_ev(
            full_probs.overall_race, camel, num_winner_bets_placed
        )
        actions.append(ActionEV(
            action_description=f"Overall winner: {camel.value}",
            expected_value=ev
        ))

    # Overall loser bets
    for camel in available_finish_cards:
        ev = calculate_overall_loser_bet_ev(
            full_probs.overall_race, camel, num_loser_bets_placed
        )
        actions.append(ActionEV(
            action_description=f"Overall loser: {camel.value}",
            expected_value=ev
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
