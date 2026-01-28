"""Tests for probability calculator."""

import pytest
from src.game.board import Board
from src.game.camel import CamelColor, CamelPositions, RACING_CAMELS
from src.game.dice import DieColor
from src.probability.calculator import (
    enumerate_dice_sequences,
    enumerate_grey_die_outcomes,
    simulate_sequence_with_grey,
    calculate_ranking_probabilities,
    LegOutcome,
    RankingProbabilities
)
from src.probability.ev import (
    calculate_leg_ticket_ev,
    calculate_all_leg_ticket_evs,
    rank_actions_by_ev,
    BettingEVs
)


class TestEnumeration:
    """Tests for dice sequence enumeration."""

    def test_enumerate_single_die(self):
        """Single die has 3 possible outcomes."""
        sequences = enumerate_dice_sequences([DieColor.BLUE])
        assert len(sequences) == 3  # values 1, 2, 3
        
        values = [seq[0][1] for seq in sequences]
        assert set(values) == {1, 2, 3}

    def test_enumerate_two_dice(self):
        """Two dice: 2! orderings x 3^2 values = 18 outcomes."""
        sequences = enumerate_dice_sequences([DieColor.BLUE, DieColor.GREEN])
        assert len(sequences) == 2 * 9  # 2! x 3^2 = 18

    def test_enumerate_three_dice(self):
        """Three dice: 3! x 3^3 = 162 outcomes."""
        sequences = enumerate_dice_sequences([DieColor.BLUE, DieColor.GREEN, DieColor.RED])
        assert len(sequences) == 6 * 27  # 3! x 3^3 = 162

    def test_enumerate_five_dice(self):
        """Five dice: 5! x 3^5 = 29,160 outcomes."""
        all_racing = [DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, 
                      DieColor.RED, DieColor.PURPLE]
        sequences = enumerate_dice_sequences(all_racing)
        assert len(sequences) == 120 * 243  # 5! x 3^5 = 29,160

    def test_enumerate_empty(self):
        """No dice returns single empty sequence."""
        sequences = enumerate_dice_sequences([])
        assert len(sequences) == 1
        assert sequences[0] == ()

    def test_grey_die_outcomes(self):
        """Grey die has 6 outcomes (2 camels x 3 values)."""
        outcomes = enumerate_grey_die_outcomes()
        assert len(outcomes) == 6
        
        # Check all combinations present
        for camel in [CamelColor.WHITE, CamelColor.BLACK]:
            for value in [1, 2, 3]:
                assert (camel, value) in outcomes


class TestSimulation:
    """Tests for sequence simulation."""

    def test_simulate_single_move(self):
        """Simulate a single die roll."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 2)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Blue moves 2 spaces: 3 -> 5
        sequence = ((DieColor.BLUE, 2),)
        outcome = simulate_sequence_with_grey(board, sequence, None, None)

        # Blue (at 5) should be ahead of Green (at 2)
        assert outcome.first == CamelColor.BLUE
        assert outcome.second == CamelColor.GREEN

    def test_simulate_overtake(self):
        """Simulate one camel overtaking another."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 5)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Blue moves 3: 3 -> 6, overtakes Green at 5
        sequence = ((DieColor.BLUE, 3),)
        outcome = simulate_sequence_with_grey(board, sequence, None, None)

        assert outcome.first == CamelColor.BLUE
        assert outcome.second == CamelColor.GREEN

    def test_simulate_with_stacking(self):
        """Simulate movement with camel stacking."""
        positions = CamelPositions.create_empty()
        # Blue at 3, Green on top of Blue
        positions = positions.place_camel(CamelColor.BLUE, 3)
        positions = positions.place_camel(CamelColor.GREEN, 3)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Blue moves 2: carries Green, both at 5
        # Green is still on top, so Green is first
        sequence = ((DieColor.BLUE, 2),)
        outcome = simulate_sequence_with_grey(board, sequence, None, None)

        assert outcome.first == CamelColor.GREEN
        assert outcome.second == CamelColor.BLUE


class TestProbabilityCalculation:
    """Tests for probability calculations."""

    def test_probabilities_sum_to_one(self):
        """Probabilities for each position should sum to 1."""
        positions = CamelPositions.create_empty()
        for i, camel in enumerate(RACING_CAMELS):
            positions = positions.place_camel(camel, i + 1)
        board = Board(camel_positions=positions, spectator_tiles={})

        # Calculate with just one die remaining (faster)
        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE],
            grey_die_available=False
        )

        # Sum of P(camel is 1st) across all camels should be 1
        sum_first = sum(probs.prob_first(c) for c in RACING_CAMELS)
        assert abs(sum_first - 1.0) < 0.0001

        # Sum of P(camel is 2nd) across all camels should be 1
        sum_second = sum(probs.prob_second(c) for c in RACING_CAMELS)
        assert abs(sum_second - 1.0) < 0.0001

    def test_leader_has_high_probability(self):
        """Camel far ahead should have high win probability."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 14)  # Near finish
        positions = positions.place_camel(CamelColor.GREEN, 2)  # Far behind
        positions = positions.place_camel(CamelColor.RED, 1)
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE],
            grey_die_available=False
        )

        # Blue should have very high probability of winning
        assert probs.prob_first(CamelColor.BLUE) > 0.9

    def test_tied_camels_split_probability(self):
        """Camels at same position should have similar probabilities."""
        positions = CamelPositions.create_empty()
        # All camels at same space, Blue at bottom, Purple at top
        for camel in [CamelColor.BLUE, CamelColor.GREEN, CamelColor.YELLOW,
                      CamelColor.RED, CamelColor.PURPLE]:
            positions = positions.place_camel(camel, 5)
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE],
            grey_die_available=False
        )

        # Top of stack (Purple) should have highest probability
        # Bottom (Blue) should have lowest
        assert probs.prob_first(CamelColor.PURPLE) > probs.prob_first(CamelColor.BLUE)


class TestExpectedValue:
    """Tests for EV calculations."""

    def test_ev_for_guaranteed_winner(self):
        """EV for betting on guaranteed winner should be ticket value."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 16)  # About to finish
        positions = positions.place_camel(CamelColor.GREEN, 1)
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE],
            grey_die_available=False
        )

        # Blue is guaranteed to win (100%)
        ev = calculate_leg_ticket_ev(probs, CamelColor.BLUE, ticket_value=5)
        assert ev == pytest.approx(5.0, abs=0.01)

    def test_ev_for_guaranteed_loser(self):
        """EV for betting on guaranteed loser should be -1."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 16)  # About to finish
        positions = positions.place_camel(CamelColor.GREEN, 15)
        positions = positions.place_camel(CamelColor.RED, 1)  # Far behind
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.RED],
            grey_die_available=False
        )

        # Red has 0% chance of top 2 (Blue and Green are too far ahead)
        ev = calculate_leg_ticket_ev(probs, CamelColor.RED, ticket_value=5)
        # Should be close to -1 (guaranteed loss)
        assert ev < 0

    def test_rank_actions(self):
        """Actions should be ranked by EV."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 10)
        positions = positions.place_camel(CamelColor.GREEN, 5)
        board = Board(camel_positions=positions, spectator_tiles={})

        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE, DieColor.GREEN],
            grey_die_available=False
        )

        available_tickets = {
            CamelColor.BLUE: (5, 3, 2, 2),
            CamelColor.GREEN: (5, 3, 2, 2),
        }

        actions = rank_actions_by_ev(probs, available_tickets)

        # Should be sorted by EV (highest first)
        evs = [a.expected_value for a in actions]
        assert evs == sorted(evs, reverse=True)

        # Betting on leader (Blue) should have higher EV than trailer (Green)
        blue_ev = next(a.expected_value for a in actions if "blue" in a.action_description.lower())
        green_ev = next(a.expected_value for a in actions if "green" in a.action_description.lower())
        assert blue_ev > green_ev


class TestIntegration:
    """Integration tests for full probability calculation."""

    def test_full_leg_calculation(self):
        """Calculate probabilities for a realistic game state."""
        positions = CamelPositions.create_empty()
        positions = positions.place_camel(CamelColor.BLUE, 5)
        positions = positions.place_camel(CamelColor.GREEN, 4)
        positions = positions.place_camel(CamelColor.YELLOW, 3)
        positions = positions.place_camel(CamelColor.RED, 2)
        positions = positions.place_camel(CamelColor.PURPLE, 1)
        board = Board(camel_positions=positions, spectator_tiles={})

        # With 2 dice remaining (manageable for testing)
        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE, DieColor.GREEN],
            grey_die_available=False
        )

        # Basic sanity checks
        for camel in RACING_CAMELS:
            p_first = probs.prob_first(camel)
            p_second = probs.prob_second(camel)
            
            # Probabilities should be between 0 and 1
            assert 0 <= p_first <= 1
            assert 0 <= p_second <= 1
            
            # Sum should not exceed 1
            assert p_first + p_second <= 1.0001

    def test_performance_three_dice(self):
        """Three dice calculation should complete quickly."""
        import time
        
        positions = CamelPositions.create_empty()
        for i, camel in enumerate(RACING_CAMELS):
            positions = positions.place_camel(camel, i + 1)
        board = Board(camel_positions=positions, spectator_tiles={})

        start = time.time()
        probs = calculate_ranking_probabilities(
            board=board,
            remaining_racing_dice=[DieColor.BLUE, DieColor.GREEN, DieColor.RED],
            grey_die_available=False
        )
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0
        
        # Results should be valid
        assert sum(probs.prob_first(c) for c in RACING_CAMELS) == pytest.approx(1.0, abs=0.001)
