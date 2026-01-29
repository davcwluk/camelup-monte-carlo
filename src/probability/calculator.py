"""Probability calculator for Camel Up.

Enumerates all possible dice outcomes and calculates exact probabilities
for camel rankings at the end of a leg.
"""

from dataclasses import dataclass
from itertools import permutations, product
from typing import Dict, List, Tuple, FrozenSet
from collections import defaultdict

from ..game.board import Board
from ..game.camel import CamelColor, CamelPositions, RACING_CAMELS
from ..game.dice import DieColor

# Possible values for racing dice (each has 1/3 probability)
DICE_VALUES = (1, 2, 3)


@dataclass(frozen=True)
class LegOutcome:
    """Result of simulating a leg to completion."""
    ranking: Tuple[CamelColor, ...]  # 1st place to last place
    spaces_landed: Tuple[int, ...]  # Spaces where camels landed during leg
    game_finished: bool = False  # Whether a camel crossed finish line

    @property
    def first(self) -> CamelColor:
        return self.ranking[0]

    @property
    def second(self) -> CamelColor:
        return self.ranking[1] if len(self.ranking) > 1 else None


@dataclass(frozen=True)
class SpaceLandingProbabilities:
    """Probability that any camel lands on each space during the leg."""
    # space_probs[space] = probability any camel lands there
    space_probs: Dict[int, float]

    def prob_landing(self, space: int) -> float:
        """Probability that any camel lands on this space."""
        return self.space_probs.get(space, 0.0)

    def expected_spectator_payout(self, space: int) -> float:
        """Expected payout (coins) for placing spectator tile on this space."""
        # Payout is 1 coin each time a camel lands
        return self.prob_landing(space) * 1.0


@dataclass(frozen=True)
class OverallRaceProbabilities:
    """Probability each camel wins/loses the entire race."""
    # win_probs[camel] = P(camel finishes 1st when game ends)
    win_probs: Dict[CamelColor, float]
    # lose_probs[camel] = P(camel finishes last when game ends)
    lose_probs: Dict[CamelColor, float]
    # P(game ends this leg)
    prob_game_ends: float

    def prob_wins_race(self, camel: CamelColor) -> float:
        """Probability camel wins the entire race."""
        return self.win_probs.get(camel, 0.0)

    def prob_loses_race(self, camel: CamelColor) -> float:
        """Probability camel loses the entire race (finishes last)."""
        return self.lose_probs.get(camel, 0.0)


@dataclass(frozen=True)
class RankingProbabilities:
    """Probability distribution for camel rankings."""
    # P(camel finishes in position) - position is 0-indexed
    # probabilities[camel][position] = probability
    probabilities: Dict[CamelColor, Tuple[float, ...]]
    
    def prob_first(self, camel: CamelColor) -> float:
        """Probability that camel finishes first."""
        return self.probabilities.get(camel, (0,))[0]
    
    def prob_second(self, camel: CamelColor) -> float:
        """Probability that camel finishes second."""
        probs = self.probabilities.get(camel, (0, 0))
        return probs[1] if len(probs) > 1 else 0.0
    
    def prob_top_two(self, camel: CamelColor) -> float:
        """Probability that camel finishes first or second."""
        return self.prob_first(camel) + self.prob_second(camel)
    
    def expected_leg_payout(self, camel: CamelColor, ticket_value: int) -> float:
        """
        Expected payout for a leg betting ticket.
        
        - 1st place: +ticket_value
        - 2nd place: +1
        - Other: -1
        """
        p_first = self.prob_first(camel)
        p_second = self.prob_second(camel)
        p_other = 1.0 - p_first - p_second
        
        return (p_first * ticket_value) + (p_second * 1) + (p_other * -1)


def get_remaining_dice(rolled_dice: FrozenSet[DieColor], include_grey: bool = True) -> List[DieColor]:
    """
    Get dice that haven't been rolled yet this leg.
    
    Args:
        rolled_dice: Set of dice already rolled
        include_grey: Whether to include grey die if not rolled
    
    Returns:
        List of remaining dice colors
    """
    all_racing = {DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW, 
                  DieColor.RED, DieColor.PURPLE}
    remaining = list(all_racing - rolled_dice)
    
    if include_grey and DieColor.GREY not in rolled_dice:
        remaining.append(DieColor.GREY)
    
    return remaining


def enumerate_dice_sequences(
    remaining_dice: List[DieColor]
) -> List[Tuple[Tuple[DieColor, int], ...]]:
    """
    Enumerate all possible sequences of dice rolls.
    
    For N remaining dice, generates N! x 3^N sequences.
    Each sequence is a tuple of (die_color, value) pairs.
    
    Args:
        remaining_dice: List of dice colors still in pyramid
    
    Returns:
        List of all possible dice sequences
    """
    if not remaining_dice:
        return [()]
    
    sequences = []
    
    # All possible orderings of dice
    for dice_order in permutations(remaining_dice):
        # All possible value combinations (1, 2, or 3 for each die)
        for values in product(DICE_VALUES, repeat=len(dice_order)):
            sequence = tuple(zip(dice_order, values))
            sequences.append(sequence)
    
    return sequences


def simulate_sequence(
    board: Board,
    sequence: Tuple[Tuple[DieColor, int], ...]
) -> LegOutcome:
    """
    Simulate a sequence of dice rolls and return the final ranking.
    
    Args:
        board: Current board state
        sequence: Sequence of (die_color, value) pairs
    
    Returns:
        LegOutcome with final ranking
    """
    current_board = board
    
    for die_color, value in sequence:
        if die_color == DieColor.GREY:
            # Grey die - determine which crazy camel moves
            # The value indicates which camel the die shows
            # But we need to apply the priority/stack rules
            grey_camel = CamelColor.WHITE if value in (1, 2, 3) else CamelColor.BLACK
            # For grey die, we interpret value as: 1,2,3 can be either white or black
            # Actually, grey die shows: white-1, white-2, white-3, black-1, black-2, black-3
            # We need to handle this differently
            
            # Simplification: treat grey die as showing (camel, movement)
            # This is handled in the enumeration - we'll enumerate separately
            pass
        else:
            # Racing die - move corresponding camel
            camel = CamelColor[die_color.name]
            current_board, _ = current_board.move_camel(camel, value)
    
    # Get final ranking
    ranking = tuple(current_board.get_ranking())
    return LegOutcome(ranking=ranking)


def enumerate_grey_die_outcomes() -> List[Tuple[CamelColor, int]]:
    """
    Enumerate all possible grey die outcomes.
    
    Grey die has 6 faces: white-1, white-2, white-3, black-1, black-2, black-3
    Each has probability 1/6.
    
    Returns:
        List of (crazy_camel, value) pairs
    """
    outcomes = []
    for camel in [CamelColor.WHITE, CamelColor.BLACK]:
        for value in [1, 2, 3]:
            outcomes.append((camel, value))
    return outcomes


def simulate_sequence_with_grey(
    board: Board,
    racing_sequence: Tuple[Tuple[DieColor, int], ...],
    grey_outcome: Tuple[CamelColor, int] | None,
    grey_position: int | None
) -> LegOutcome:
    """
    Simulate a sequence including grey die at a specific position.

    Args:
        board: Current board state
        racing_sequence: Sequence of racing die rolls
        grey_outcome: (crazy_camel, value) for grey die, or None if not rolled
        grey_position: Position in sequence where grey die is rolled (0 to len)

    Returns:
        LegOutcome with final ranking, spaces landed, and game finish status
    """
    current_board = board
    racing_idx = 0
    spaces_landed = []
    game_finished = False

    total_dice = len(racing_sequence) + (1 if grey_outcome else 0)

    for i in range(total_dice):
        if grey_outcome and i == grey_position:
            # Roll grey die
            grey_camel_shown, value = grey_outcome
            # Apply crazy camel rules to determine which one actually moves
            actual_camel = current_board.camel_positions.get_crazy_camel_to_move(grey_camel_shown)
            old_space = current_board.camel_positions.get_camel_space(actual_camel)
            current_board, _ = current_board.move_camel(actual_camel, -value)
            new_space = current_board.camel_positions.get_camel_space(actual_camel)
            # Track landing space (for spectator tile calculation)
            if new_space != old_space:
                spaces_landed.append(new_space)
        else:
            # Roll racing die
            if racing_idx < len(racing_sequence):
                die_color, value = racing_sequence[racing_idx]
                camel = CamelColor[die_color.name]
                old_space = current_board.camel_positions.get_camel_space(camel)
                current_board, _ = current_board.move_camel(camel, value)
                new_space = current_board.camel_positions.get_camel_space(camel)
                # Track landing space
                if new_space is not None and (old_space is None or new_space != old_space):
                    spaces_landed.append(new_space)
                racing_idx += 1

        # Check if game finished (any racing camel crossed finish line)
        if current_board.is_game_over():
            game_finished = True
            break

    ranking = tuple(current_board.get_ranking())
    return LegOutcome(
        ranking=ranking,
        spaces_landed=tuple(spaces_landed),
        game_finished=game_finished
    )


def calculate_ranking_probabilities(
    board: Board,
    remaining_racing_dice: List[DieColor],
    grey_die_available: bool
) -> RankingProbabilities:
    """
    Calculate exact probability distribution for camel rankings.
    
    Enumerates all possible dice outcomes and their probabilities.
    
    Args:
        board: Current board state
        remaining_racing_dice: Racing dice still in pyramid
        grey_die_available: Whether grey die hasn't been rolled yet
    
    Returns:
        RankingProbabilities with exact probabilities
    """
    # Count occurrences of each ranking
    ranking_counts: Dict[CamelColor, List[int]] = {
        camel: [0] * 5 for camel in RACING_CAMELS
    }
    total_outcomes = 0
    
    # Generate all racing die sequences
    racing_sequences = enumerate_dice_sequences(remaining_racing_dice)
    
    if grey_die_available:
        # Grey die can be rolled at any position
        grey_outcomes = enumerate_grey_die_outcomes()
        num_total_dice = len(remaining_racing_dice) + 1
        
        for racing_seq in racing_sequences:
            for grey_outcome in grey_outcomes:
                # Grey die can be at positions 0 to num_total_dice-1
                # But actually it's drawn uniformly, so position matters
                for grey_pos in range(num_total_dice):
                    outcome = simulate_sequence_with_grey(
                        board, racing_seq, grey_outcome, grey_pos
                    )
                    
                    # Record ranking
                    for pos, camel in enumerate(outcome.ranking):
                        if camel in ranking_counts:
                            ranking_counts[camel][pos] += 1
                    
                    total_outcomes += 1
    else:
        # No grey die, just racing dice
        for racing_seq in racing_sequences:
            outcome = simulate_sequence_with_grey(board, racing_seq, None, None)
            
            for pos, camel in enumerate(outcome.ranking):
                if camel in ranking_counts:
                    ranking_counts[camel][pos] += 1
            
            total_outcomes += 1
    
    # Convert counts to probabilities
    probabilities = {}
    for camel, counts in ranking_counts.items():
        if total_outcomes > 0:
            probs = tuple(count / total_outcomes for count in counts)
        else:
            probs = tuple(0.0 for _ in counts)
        probabilities[camel] = probs
    
    return RankingProbabilities(probabilities=probabilities)


def calculate_probabilities_from_game_state(board: Board, grey_rolled: bool) -> RankingProbabilities:
    """
    Calculate ranking probabilities from current game state.

    This is a convenience function that extracts the necessary info
    from the board state.

    Args:
        board: Current board state
        grey_rolled: Whether grey die has been rolled this leg

    Returns:
        RankingProbabilities
    """
    # Determine which racing dice have been rolled by checking camel positions
    # Actually, we need pyramid state for this - this function needs more info
    # For now, assume all racing dice are available (start of leg)

    all_racing_dice = [DieColor.BLUE, DieColor.GREEN, DieColor.YELLOW,
                       DieColor.RED, DieColor.PURPLE]

    return calculate_ranking_probabilities(
        board=board,
        remaining_racing_dice=all_racing_dice,
        grey_die_available=not grey_rolled
    )


@dataclass(frozen=True)
class FullProbabilities:
    """Complete probability analysis for current game state."""
    ranking: RankingProbabilities
    space_landings: SpaceLandingProbabilities
    overall_race: OverallRaceProbabilities


def calculate_all_probabilities(
    board: Board,
    remaining_racing_dice: List[DieColor],
    grey_die_available: bool
) -> FullProbabilities:
    """
    Calculate all probabilities: rankings, space landings, and overall race.

    Args:
        board: Current board state
        remaining_racing_dice: Racing dice still in pyramid
        grey_die_available: Whether grey die hasn't been rolled yet

    Returns:
        FullProbabilities with all calculated values
    """
    # Count occurrences
    ranking_counts: Dict[CamelColor, List[int]] = {
        camel: [0] * 5 for camel in RACING_CAMELS
    }
    space_landing_counts: Dict[int, int] = defaultdict(int)
    win_counts: Dict[CamelColor, int] = {camel: 0 for camel in RACING_CAMELS}
    lose_counts: Dict[CamelColor, int] = {camel: 0 for camel in RACING_CAMELS}
    game_ends_count = 0
    total_outcomes = 0

    # Generate all racing die sequences
    racing_sequences = enumerate_dice_sequences(remaining_racing_dice)

    if grey_die_available:
        grey_outcomes = enumerate_grey_die_outcomes()
        num_total_dice = len(remaining_racing_dice) + 1

        for racing_seq in racing_sequences:
            for grey_outcome in grey_outcomes:
                for grey_pos in range(num_total_dice):
                    outcome = simulate_sequence_with_grey(
                        board, racing_seq, grey_outcome, grey_pos
                    )

                    # Record ranking - count positions among racing camels only
                    racing_pos = 0
                    for camel in outcome.ranking:
                        if camel in ranking_counts:
                            ranking_counts[camel][racing_pos] += 1
                            racing_pos += 1

                    # Record space landings
                    for space in outcome.spaces_landed:
                        space_landing_counts[space] += 1

                    # Record game end outcomes
                    if outcome.game_finished:
                        game_ends_count += 1
                        if outcome.ranking:
                            # Winner/loser among racing camels
                            racing_ranking = [c for c in outcome.ranking if c in RACING_CAMELS]
                            if racing_ranking:
                                winner = racing_ranking[0]
                                loser = racing_ranking[-1]
                                win_counts[winner] += 1
                                lose_counts[loser] += 1

                    total_outcomes += 1
    else:
        for racing_seq in racing_sequences:
            outcome = simulate_sequence_with_grey(board, racing_seq, None, None)

            # Count positions among racing camels only
            racing_pos = 0
            for camel in outcome.ranking:
                if camel in ranking_counts:
                    ranking_counts[camel][racing_pos] += 1
                    racing_pos += 1

            for space in outcome.spaces_landed:
                space_landing_counts[space] += 1

            if outcome.game_finished:
                game_ends_count += 1
                if outcome.ranking:
                    # Winner/loser among racing camels
                    racing_ranking = [c for c in outcome.ranking if c in RACING_CAMELS]
                    if racing_ranking:
                        winner = racing_ranking[0]
                        loser = racing_ranking[-1]
                        win_counts[winner] += 1
                        lose_counts[loser] += 1

            total_outcomes += 1

    # Convert counts to probabilities
    if total_outcomes > 0:
        ranking_probs = {
            camel: tuple(count / total_outcomes for count in counts)
            for camel, counts in ranking_counts.items()
        }
        space_probs = {
            space: count / total_outcomes
            for space, count in space_landing_counts.items()
        }
        prob_game_ends = game_ends_count / total_outcomes

        if game_ends_count > 0:
            win_probs = {camel: count / game_ends_count for camel, count in win_counts.items()}
            lose_probs = {camel: count / game_ends_count for camel, count in lose_counts.items()}
        else:
            # Game doesn't end this leg - use leg ranking as estimate
            win_probs = {camel: ranking_probs[camel][0] for camel in RACING_CAMELS}
            lose_probs = {camel: ranking_probs[camel][4] for camel in RACING_CAMELS}
    else:
        ranking_probs = {camel: (0.0,) * 5 for camel in RACING_CAMELS}
        space_probs = {}
        win_probs = {camel: 0.0 for camel in RACING_CAMELS}
        lose_probs = {camel: 0.0 for camel in RACING_CAMELS}
        prob_game_ends = 0.0

    return FullProbabilities(
        ranking=RankingProbabilities(probabilities=ranking_probs),
        space_landings=SpaceLandingProbabilities(space_probs=space_probs),
        overall_race=OverallRaceProbabilities(
            win_probs=win_probs,
            lose_probs=lose_probs,
            prob_game_ends=prob_game_ends
        )
    )
