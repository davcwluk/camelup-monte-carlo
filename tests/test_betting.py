"""Tests for betting tickets and scoring mechanics."""

import pytest
from src.game.betting import (
    BettingState, BettingTicket, PlayerState, OverallBet,
    calculate_leg_scores, calculate_overall_scores,
    TICKET_VALUES, OVERALL_PAYOUTS
)
from src.game.camel import CamelColor, RACING_CAMELS


class TestBettingTickets:
    """Tests for leg betting ticket mechanics."""

    def test_ticket_values_are_5_3_2_2(self):
        """Betting tickets have values 5, 3, 2, 2 (top to bottom)."""
        assert TICKET_VALUES == (5, 3, 2, 2)

    def test_four_tickets_per_camel(self):
        """Each camel color has 4 betting tickets."""
        state = BettingState.create_for_players(2)
        for camel in RACING_CAMELS:
            assert len(state.available_tickets[camel]) == 4

    def test_take_top_ticket_gets_highest_value(self):
        """Taking a ticket gets the top one (highest value first)."""
        state = BettingState.create_for_players(2)

        # First ticket should be worth 5
        ticket = state.get_available_ticket(CamelColor.BLUE)
        assert ticket.value == 5

        # Take it
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)

        # Next ticket should be worth 3
        ticket = state.get_available_ticket(CamelColor.BLUE)
        assert ticket.value == 3

    def test_ticket_removed_when_taken(self):
        """Taking a ticket removes it from available stack."""
        state = BettingState.create_for_players(2)

        assert len(state.available_tickets[CamelColor.BLUE]) == 4
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)
        assert len(state.available_tickets[CamelColor.BLUE]) == 3

    def test_can_take_multiple_tickets_same_camel(self):
        """Player can take multiple tickets for the same camel."""
        state = BettingState.create_for_players(2)

        state = state.take_ticket(player=0, camel=CamelColor.BLUE)
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)

        # Player should have 3 blue tickets
        player_tickets = state.player_tickets[0]
        blue_tickets = [t for t in player_tickets if t.camel == CamelColor.BLUE]
        assert len(blue_tickets) == 3
        assert [t.value for t in blue_tickets] == [5, 3, 2]

    def test_no_ticket_available_when_all_taken(self):
        """Returns None when all tickets for a camel are taken."""
        state = BettingState.create_for_players(2)

        # Take all 4 blue tickets
        for _ in range(4):
            state = state.take_ticket(player=0, camel=CamelColor.BLUE)

        assert state.get_available_ticket(CamelColor.BLUE) is None

    def test_get_all_available_tickets(self):
        """Get all available tickets across all camels."""
        state = BettingState.create_for_players(2)

        tickets = state.get_all_available_tickets()
        assert len(tickets) == 5  # One per camel (top ticket only)

        # All should be worth 5 (top ticket)
        for ticket in tickets:
            assert ticket.value == 5


class TestPyramidTickets:
    """Tests for pyramid ticket mechanics."""

    def test_pyramid_ticket_increments_count(self):
        """Taking pyramid ticket increments player's count."""
        state = BettingState.create_for_players(2)

        assert state.player_pyramid_tickets[0] == 0
        state = state.take_pyramid_ticket(player=0)
        assert state.player_pyramid_tickets[0] == 1
        state = state.take_pyramid_ticket(player=0)
        assert state.player_pyramid_tickets[0] == 2

    def test_pyramid_tickets_per_player(self):
        """Each player tracks their own pyramid tickets."""
        state = BettingState.create_for_players(3)

        state = state.take_pyramid_ticket(player=0)
        state = state.take_pyramid_ticket(player=0)
        state = state.take_pyramid_ticket(player=1)

        assert state.player_pyramid_tickets[0] == 2
        assert state.player_pyramid_tickets[1] == 1
        assert state.player_pyramid_tickets[2] == 0


class TestLegScoring:
    """Tests for leg-end scoring."""

    def test_first_place_bet_earns_ticket_value(self):
        """Correct 1st place bet earns the ticket's face value."""
        state = BettingState.create_for_players(2)
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)  # 5-point ticket

        scores = calculate_leg_scores(
            state,
            first_place=CamelColor.BLUE,
            second_place=CamelColor.GREEN
        )

        assert scores[0] == 5  # Player 0 bet on winner, gets ticket value

    def test_second_place_bet_earns_one(self):
        """Correct 2nd place bet earns 1 coin."""
        state = BettingState.create_for_players(2)
        state = state.take_ticket(player=0, camel=CamelColor.GREEN)  # 5-point ticket

        scores = calculate_leg_scores(
            state,
            first_place=CamelColor.BLUE,
            second_place=CamelColor.GREEN
        )

        assert scores[0] == 1  # Player 0 bet on 2nd place

    def test_other_place_bet_loses_one(self):
        """Bet on 3rd-5th place loses 1 coin."""
        state = BettingState.create_for_players(2)
        state = state.take_ticket(player=0, camel=CamelColor.RED)  # Bet on Red

        scores = calculate_leg_scores(
            state,
            first_place=CamelColor.BLUE,
            second_place=CamelColor.GREEN
        )

        assert scores[0] == -1  # Red not in top 2

    def test_pyramid_ticket_earns_one_each(self):
        """Each pyramid ticket earns 1 coin."""
        state = BettingState.create_for_players(2)
        state = state.take_pyramid_ticket(player=0)
        state = state.take_pyramid_ticket(player=0)
        state = state.take_pyramid_ticket(player=0)

        scores = calculate_leg_scores(
            state,
            first_place=CamelColor.BLUE,
            second_place=CamelColor.GREEN
        )

        assert scores[0] == 3  # 3 pyramid tickets = 3 coins

    def test_combined_leg_scoring(self):
        """Multiple bets and pyramid tickets combine correctly."""
        state = BettingState.create_for_players(2)

        # Player 0: bet on Blue (5pt), bet on Green (3pt), 2 pyramid tickets
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)
        state = state.take_ticket(player=0, camel=CamelColor.GREEN)
        state = state.take_pyramid_ticket(player=0)
        state = state.take_pyramid_ticket(player=0)

        # Player 1: bet on Red (5pt)
        state = state.take_ticket(player=1, camel=CamelColor.RED)

        scores = calculate_leg_scores(
            state,
            first_place=CamelColor.BLUE,  # Player 0's Blue bet wins
            second_place=CamelColor.GREEN  # Player 0's Green bet = 2nd
        )

        # Player 0: 5 (Blue 1st) + 1 (Green 2nd) + 2 (pyramid) = 8
        assert scores[0] == 8
        # Player 1: -1 (Red not in top 2)
        assert scores[1] == -1

    def test_tickets_reset_after_leg(self):
        """Betting state reset returns tickets to stacks."""
        state = BettingState.create_for_players(2)
        state = state.take_ticket(player=0, camel=CamelColor.BLUE)
        state = state.take_pyramid_ticket(player=0)

        # Reset for new leg
        state = state.reset_for_new_leg()

        # Tickets should be back
        assert len(state.available_tickets[CamelColor.BLUE]) == 4
        # Player tickets cleared
        assert len(state.player_tickets[0]) == 0
        # Pyramid tickets cleared
        assert state.player_pyramid_tickets[0] == 0


class TestOverallBetting:
    """Tests for overall winner/loser betting."""

    def test_player_has_five_finish_cards(self):
        """Each player starts with 5 finish cards (one per racing camel)."""
        player = PlayerState()
        assert len(player.available_finish_cards) == 5
        for camel in RACING_CAMELS:
            assert camel in player.available_finish_cards

    def test_finish_card_removed_when_used(self):
        """Using a finish card removes it from available."""
        player = PlayerState()
        player = player.use_finish_card(CamelColor.BLUE)

        assert CamelColor.BLUE not in player.available_finish_cards
        assert len(player.available_finish_cards) == 4

    def test_can_bet_winner_or_loser(self):
        """Can bet on winner or loser with finish cards."""
        state = BettingState.create_for_players(2)

        state = state.place_overall_bet(player=0, camel=CamelColor.BLUE, is_winner_bet=True)
        state = state.place_overall_bet(player=1, camel=CamelColor.RED, is_winner_bet=False)

        assert len(state.winner_bets) == 1
        assert state.winner_bets[0].camel == CamelColor.BLUE
        assert len(state.loser_bets) == 1
        assert state.loser_bets[0].camel == CamelColor.RED

    def test_overall_payouts_structure(self):
        """Overall payouts are 8, 5, 3, 2, 1, 1, 1, 1."""
        assert OVERALL_PAYOUTS == (8, 5, 3, 2, 1, 1, 1, 1)

    def test_first_correct_winner_bet_earns_eight(self):
        """First correct winner bet earns 8 coins."""
        state = BettingState.create_for_players(2)
        state = state.place_overall_bet(player=0, camel=CamelColor.BLUE, is_winner_bet=True)

        scores = calculate_overall_scores(
            state,
            winner=CamelColor.BLUE,
            loser=CamelColor.RED
        )

        assert scores[0] == 8

    def test_second_correct_winner_bet_earns_five(self):
        """Second correct winner bet earns 5 coins."""
        state = BettingState.create_for_players(3)
        state = state.place_overall_bet(player=0, camel=CamelColor.BLUE, is_winner_bet=True)
        state = state.place_overall_bet(player=1, camel=CamelColor.BLUE, is_winner_bet=True)

        scores = calculate_overall_scores(
            state,
            winner=CamelColor.BLUE,
            loser=CamelColor.RED
        )

        assert scores[0] == 8  # First correct
        assert scores[1] == 5  # Second correct

    def test_correct_winner_bet_order_matters(self):
        """Payout decreases based on order of correct bets: 8, 5, 3, 2, 1..."""
        state = BettingState.create_for_players(5)

        # All 5 players bet on Blue (winner)
        for i in range(5):
            state = state.place_overall_bet(player=i, camel=CamelColor.BLUE, is_winner_bet=True)

        scores = calculate_overall_scores(
            state,
            winner=CamelColor.BLUE,
            loser=CamelColor.RED
        )

        assert scores[0] == 8  # 1st
        assert scores[1] == 5  # 2nd
        assert scores[2] == 3  # 3rd
        assert scores[3] == 2  # 4th
        assert scores[4] == 1  # 5th

    def test_wrong_winner_bet_loses_one(self):
        """Wrong winner bet loses 1 coin."""
        state = BettingState.create_for_players(2)
        state = state.place_overall_bet(player=0, camel=CamelColor.GREEN, is_winner_bet=True)

        scores = calculate_overall_scores(
            state,
            winner=CamelColor.BLUE,  # Green didn't win
            loser=CamelColor.RED
        )

        assert scores[0] == -1

    def test_loser_bet_scoring_same_as_winner(self):
        """Loser bets follow same payout structure as winner bets."""
        state = BettingState.create_for_players(3)
        state = state.place_overall_bet(player=0, camel=CamelColor.RED, is_winner_bet=False)
        state = state.place_overall_bet(player=1, camel=CamelColor.RED, is_winner_bet=False)
        state = state.place_overall_bet(player=2, camel=CamelColor.GREEN, is_winner_bet=False)

        scores = calculate_overall_scores(
            state,
            winner=CamelColor.BLUE,
            loser=CamelColor.RED
        )

        assert scores[0] == 8  # First correct loser bet
        assert scores[1] == 5  # Second correct loser bet
        assert scores[2] == -1  # Wrong loser bet

    def test_overall_bets_preserved_after_leg_reset(self):
        """Overall bets are NOT cleared when leg resets."""
        state = BettingState.create_for_players(2)
        state = state.place_overall_bet(player=0, camel=CamelColor.BLUE, is_winner_bet=True)

        state = state.reset_for_new_leg()

        # Overall bets should still be there
        assert len(state.winner_bets) == 1


class TestPlayerState:
    """Tests for player state management."""

    def test_player_starts_with_three_coins(self):
        """Each player starts with 3 coins."""
        player = PlayerState()
        assert player.coins == 3

    def test_add_coins(self):
        """Adding coins increases player's total."""
        player = PlayerState()
        player = player.add_coins(5)
        assert player.coins == 8

    def test_coins_cannot_go_below_zero(self):
        """Player cannot have negative coins."""
        player = PlayerState()
        player = player.add_coins(-10)  # Try to lose 10 coins
        assert player.coins == 0  # Floored at 0

    def test_spectator_tile_tracking(self):
        """Track whether player has placed their spectator tile."""
        player = PlayerState()
        assert player.has_spectator_tile is True

        player = player.use_spectator_tile()
        assert player.has_spectator_tile is False

        player = player.return_spectator_tile()
        assert player.has_spectator_tile is True

    def test_can_bet_on_overall_checks_cards(self):
        """can_bet_on_overall checks if finish card is available."""
        player = PlayerState()

        assert player.can_bet_on_overall(CamelColor.BLUE)
        player = player.use_finish_card(CamelColor.BLUE)
        assert not player.can_bet_on_overall(CamelColor.BLUE)
        assert player.can_bet_on_overall(CamelColor.GREEN)  # Others still ok
