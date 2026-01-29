"""Game result data classes and CSV I/O for simulation framework."""

import csv
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GameResult:
    """Result of a single game in a simulation."""
    game_index: int          # 0-based index
    seed: int                # game seed (base_seed + game_index)
    scores: Tuple[int, ...]  # final coins per seat
    winner: int | None       # winning seat index (None = tie)
    num_legs: int
    num_turns: int
    agent_names: Tuple[str, ...]  # who sits in seat 0, seat 1
    first_player: int        # 0 = agent A went first, 1 = agent B went first


@dataclass(frozen=True)
class MatchupResult:
    """Aggregated results of all games in a matchup."""
    agent_a_name: str
    agent_b_name: str
    games: Tuple[GameResult, ...]
    base_seed: int
    fast_mode: bool
    elapsed_seconds: float


_CSV_COLUMNS = [
    "game_index", "seed", "score_0", "score_1", "winner",
    "num_legs", "num_turns", "agent_seat_0", "agent_seat_1", "first_player",
]


def save_results_csv(matchup: MatchupResult, filepath: str) -> None:
    """Save matchup results to CSV file."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_COLUMNS)
        for game in matchup.games:
            writer.writerow([
                game.game_index,
                game.seed,
                game.scores[0],
                game.scores[1],
                "tie" if game.winner is None else game.winner,
                game.num_legs,
                game.num_turns,
                game.agent_names[0],
                game.agent_names[1],
                game.first_player,
            ])


def load_results_csv(filepath: str) -> MatchupResult:
    """Load matchup results from CSV file.

    Reconstructs a MatchupResult with base_seed, fast_mode, and
    elapsed_seconds set to defaults (0, False, 0.0) since those are
    not stored in the CSV.
    """
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        games = []
        agent_a_name = None
        agent_b_name = None
        base_seed = 0
        for row in reader:
            game_index = int(row["game_index"])
            seed = int(row["seed"])
            scores = (int(row["score_0"]), int(row["score_1"]))
            winner_raw = row["winner"]
            winner = None if winner_raw == "tie" else int(winner_raw)
            num_legs = int(row["num_legs"])
            num_turns = int(row["num_turns"])
            agent_names = (row["agent_seat_0"], row["agent_seat_1"])
            first_player = int(row["first_player"])

            # Determine agent A/B names from the first game
            if agent_a_name is None:
                if first_player == 0:
                    agent_a_name = agent_names[0]
                    agent_b_name = agent_names[1]
                else:
                    agent_a_name = agent_names[1]
                    agent_b_name = agent_names[0]
                base_seed = seed

            games.append(GameResult(
                game_index=game_index,
                seed=seed,
                scores=scores,
                winner=winner,
                num_legs=num_legs,
                num_turns=num_turns,
                agent_names=agent_names,
                first_player=first_player,
            ))

    return MatchupResult(
        agent_a_name=agent_a_name or "",
        agent_b_name=agent_b_name or "",
        games=tuple(games),
        base_seed=base_seed,
        fast_mode=False,
        elapsed_seconds=0.0,
    )
