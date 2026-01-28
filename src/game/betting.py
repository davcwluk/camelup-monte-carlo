"""Betting tickets and scoring for Camel Up."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .camel import CamelColor, RACING_CAMELS


# Betting ticket values (in order from top to bottom of stack)
TICKET_VALUES: Tuple[int, ...] = (5, 3, 2, 2)

# Leg scoring payouts
LEG_FIRST_PLACE_PAYOUT = TICKET_VALUES  # Same as ticket value
LEG_SECOND_PLACE_PAYOUT = 1
LEG_OTHER_PLACE_PAYOUT = -1

# Overall winner/loser payouts by position in betting order
OVERALL_PAYOUTS: Tuple[int, ...] = (8, 5, 3, 2, 1, 1, 1, 1)  # 1st correct gets 8, etc.
OVERALL_WRONG_PAYOUT = -1


@dataclass(frozen=True)
class BettingTicket:
    """A betting ticket for a camel to win the leg."""
    camel: CamelColor
    value: int  # Payout if camel wins (5, 3, 2, or 2)


@dataclass(frozen=True)
class OverallBet:
    """A bet on the overall winner or loser of the race."""
    camel: CamelColor
    player: int  # Player who placed the bet
    is_winner_bet: bool  # True = betting on winner, False = betting on loser


@dataclass(frozen=True)
class BettingState:
    """
    Tracks all betting-related state.

    - Available tickets per camel (stack from top to bottom)
    - Collected tickets per player
    - Pyramid tickets per player
    - Overall winner/loser bets
    """
    # Available tickets: maps camel color to list of remaining values
    available_tickets: Dict[CamelColor, Tuple[int, ...]] = field(
        default_factory=lambda: {
            camel: TICKET_VALUES for camel in RACING_CAMELS
        }
    )

    # Collected leg betting tickets per player
    player_tickets: Tuple[Tuple[BettingTicket, ...], ...] = ()

    # Pyramid tickets collected per player
    player_pyramid_tickets: Tuple[int, ...] = ()

    # Overall winner bets (in order placed)
    winner_bets: Tuple[OverallBet, ...] = ()

    # Overall loser bets (in order placed)
    loser_bets: Tuple[OverallBet, ...] = ()

    @classmethod
    def create_for_players(cls, num_players: int) -> "BettingState":
        """Create initial betting state for given number of players."""
        return cls(
            available_tickets={camel: TICKET_VALUES for camel in RACING_CAMELS},
            player_tickets=tuple(() for _ in range(num_players)),
            player_pyramid_tickets=tuple(0 for _ in range(num_players)),
            winner_bets=(),
            loser_bets=()
        )

    def get_available_ticket(self, camel: CamelColor) -> BettingTicket | None:
        """Get the top available ticket for a camel, if any."""
        tickets = self.available_tickets.get(camel, ())
        if tickets:
            return BettingTicket(camel=camel, value=tickets[0])
        return None

    def get_all_available_tickets(self) -> List[BettingTicket]:
        """Get all available betting tickets."""
        tickets = []
        for camel in RACING_CAMELS:
            ticket = self.get_available_ticket(camel)
            if ticket:
                tickets.append(ticket)
        return tickets

    def take_ticket(self, player: int, camel: CamelColor) -> "BettingState":
        """
        Player takes the top betting ticket for a camel.

        Returns new betting state with ticket taken.
        """
        ticket = self.get_available_ticket(camel)
        if ticket is None:
            raise ValueError(f"No tickets available for {camel}")

        if player < 0 or player >= len(self.player_tickets):
            raise ValueError(f"Invalid player index: {player}")

        # Remove ticket from available
        new_available = dict(self.available_tickets)
        new_available[camel] = self.available_tickets[camel][1:]

        # Add ticket to player's collection
        new_player_tickets = list(self.player_tickets)
        new_player_tickets[player] = self.player_tickets[player] + (ticket,)

        return BettingState(
            available_tickets=new_available,
            player_tickets=tuple(new_player_tickets),
            player_pyramid_tickets=self.player_pyramid_tickets,
            winner_bets=self.winner_bets,
            loser_bets=self.loser_bets
        )

    def take_pyramid_ticket(self, player: int) -> "BettingState":
        """Player takes a pyramid ticket (+1 coin at leg end)."""
        if player < 0 or player >= len(self.player_pyramid_tickets):
            raise ValueError(f"Invalid player index: {player}")

        new_pyramid = list(self.player_pyramid_tickets)
        new_pyramid[player] += 1

        return BettingState(
            available_tickets=self.available_tickets,
            player_tickets=self.player_tickets,
            player_pyramid_tickets=tuple(new_pyramid),
            winner_bets=self.winner_bets,
            loser_bets=self.loser_bets
        )

    def place_overall_bet(
        self,
        player: int,
        camel: CamelColor,
        is_winner_bet: bool
    ) -> "BettingState":
        """Place a bet on the overall winner or loser."""
        bet = OverallBet(camel=camel, player=player, is_winner_bet=is_winner_bet)

        if is_winner_bet:
            return BettingState(
                available_tickets=self.available_tickets,
                player_tickets=self.player_tickets,
                player_pyramid_tickets=self.player_pyramid_tickets,
                winner_bets=self.winner_bets + (bet,),
                loser_bets=self.loser_bets
            )
        else:
            return BettingState(
                available_tickets=self.available_tickets,
                player_tickets=self.player_tickets,
                player_pyramid_tickets=self.player_pyramid_tickets,
                winner_bets=self.winner_bets,
                loser_bets=self.loser_bets + (bet,)
            )

    def reset_for_new_leg(self) -> "BettingState":
        """Reset betting state for a new leg (keep overall bets)."""
        num_players = len(self.player_tickets)
        return BettingState(
            available_tickets={camel: TICKET_VALUES for camel in RACING_CAMELS},
            player_tickets=tuple(() for _ in range(num_players)),
            player_pyramid_tickets=tuple(0 for _ in range(num_players)),
            winner_bets=self.winner_bets,
            loser_bets=self.loser_bets
        )


def calculate_leg_scores(
    betting_state: BettingState,
    first_place: CamelColor,
    second_place: CamelColor
) -> Tuple[int, ...]:
    """
    Calculate scores for all players at the end of a leg.

    Returns tuple of score changes per player.
    """
    num_players = len(betting_state.player_tickets)
    scores = [0] * num_players

    for player in range(num_players):
        # Score betting tickets
        for ticket in betting_state.player_tickets[player]:
            if ticket.camel == first_place:
                scores[player] += ticket.value
            elif ticket.camel == second_place:
                scores[player] += LEG_SECOND_PLACE_PAYOUT
            else:
                scores[player] += LEG_OTHER_PLACE_PAYOUT

        # Score pyramid tickets
        scores[player] += betting_state.player_pyramid_tickets[player]

    return tuple(scores)


def calculate_overall_scores(
    betting_state: BettingState,
    winner: CamelColor,
    loser: CamelColor
) -> Tuple[int, ...]:
    """
    Calculate scores for overall winner/loser bets at game end.

    Returns tuple of score changes per player.
    """
    num_players = len(betting_state.player_tickets)
    scores = [0] * num_players

    # Score winner bets
    correct_winner_count = 0
    for bet in betting_state.winner_bets:
        if bet.camel == winner:
            # Get payout based on order (first correct gets 8, etc.)
            payout_idx = min(correct_winner_count, len(OVERALL_PAYOUTS) - 1)
            scores[bet.player] += OVERALL_PAYOUTS[payout_idx]
            correct_winner_count += 1
        else:
            scores[bet.player] += OVERALL_WRONG_PAYOUT

    # Score loser bets
    correct_loser_count = 0
    for bet in betting_state.loser_bets:
        if bet.camel == loser:
            payout_idx = min(correct_loser_count, len(OVERALL_PAYOUTS) - 1)
            scores[bet.player] += OVERALL_PAYOUTS[payout_idx]
            correct_loser_count += 1
        else:
            scores[bet.player] += OVERALL_WRONG_PAYOUT

    return tuple(scores)


@dataclass(frozen=True)
class PlayerState:
    """Complete state for a single player."""
    coins: int = 3  # Starting coins
    has_spectator_tile: bool = True  # Whether tile is available to place
    # Cards for overall betting (one per racing camel)
    available_finish_cards: Tuple[CamelColor, ...] = tuple(RACING_CAMELS)

    def add_coins(self, amount: int) -> "PlayerState":
        """Add or remove coins (capped at 0 minimum)."""
        return PlayerState(
            coins=max(0, self.coins + amount),
            has_spectator_tile=self.has_spectator_tile,
            available_finish_cards=self.available_finish_cards
        )

    def use_spectator_tile(self) -> "PlayerState":
        """Mark spectator tile as placed."""
        return PlayerState(
            coins=self.coins,
            has_spectator_tile=False,
            available_finish_cards=self.available_finish_cards
        )

    def return_spectator_tile(self) -> "PlayerState":
        """Return spectator tile (at end of leg)."""
        return PlayerState(
            coins=self.coins,
            has_spectator_tile=True,
            available_finish_cards=self.available_finish_cards
        )

    def use_finish_card(self, camel: CamelColor) -> "PlayerState":
        """Use a finish card for overall betting."""
        if camel not in self.available_finish_cards:
            raise ValueError(f"Finish card for {camel} not available")
        new_cards = tuple(c for c in self.available_finish_cards if c != camel)
        return PlayerState(
            coins=self.coins,
            has_spectator_tile=self.has_spectator_tile,
            available_finish_cards=new_cards
        )

    def can_bet_on_overall(self, camel: CamelColor) -> bool:
        """Check if player can still bet on a camel for overall winner/loser."""
        return camel in self.available_finish_cards
