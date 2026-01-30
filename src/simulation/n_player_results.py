"""N-player game result data class and CSV I/O for simulation framework."""

import csv
from dataclasses import dataclass
from typing import Tuple

from src.simulation.results import GameResult


@dataclass(frozen=True)
class NPlayerMatchupResult:
    """Aggregated results of all games in an N-player matchup.

    Models a focal agent vs a field of opponents, rather than the
    paired A-vs-B comparison used in 2-player MatchupResult.
    """
    focal_agent_name: str
    field_agent_names: Tuple[str, ...]
    num_players: int
    games: Tuple[GameResult, ...]
    base_seed: int
    fast_mode: bool
    elapsed_seconds: float


def save_n_player_results_csv(result: NPlayerMatchupResult, filepath: str) -> None:
    """Save N-player matchup results to CSV file.

    Columns are dynamic based on num_players:
    game_index, seed, score_0..score_{N-1}, winner, num_legs, num_turns,
    agent_seat_0..agent_seat_{N-1}, focal_seat
    """
    n = result.num_players
    columns = ["game_index", "seed"]
    columns += [f"score_{i}" for i in range(n)]
    columns += ["winner", "num_legs", "num_turns"]
    columns += [f"agent_seat_{i}" for i in range(n)]
    columns += ["focal_seat"]

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for game in result.games:
            row = [game.game_index, game.seed]
            row += [game.scores[i] for i in range(n)]
            row.append("tie" if game.winner is None else game.winner)
            row += [game.num_legs, game.num_turns]
            row += [game.agent_names[i] for i in range(n)]
            row.append(game.first_player)
            writer.writerow(row)


def load_n_player_results_csv(filepath: str) -> NPlayerMatchupResult:
    """Load N-player matchup results from CSV file.

    Auto-detects num_players from the number of score_* columns.
    Metadata fields (base_seed, fast_mode, elapsed_seconds) are set to
    defaults since they are not stored in the CSV.
    """
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Detect N from score columns
        n = 0
        while f"score_{n}" in fieldnames:
            n += 1

        games = []
        focal_agent_name = None
        field_agent_names = None
        base_seed = 0

        for row in reader:
            game_index = int(row["game_index"])
            seed = int(row["seed"])
            scores = tuple(int(row[f"score_{i}"]) for i in range(n))
            winner_raw = row["winner"]
            winner = None if winner_raw == "tie" else int(winner_raw)
            num_legs = int(row["num_legs"])
            num_turns = int(row["num_turns"])
            agent_names = tuple(row[f"agent_seat_{i}"] for i in range(n))
            focal_seat = int(row["focal_seat"])

            if focal_agent_name is None:
                focal_agent_name = agent_names[focal_seat]
                field_agent_names = tuple(
                    agent_names[i] for i in range(n) if i != focal_seat
                )
                base_seed = seed

            games.append(GameResult(
                game_index=game_index,
                seed=seed,
                scores=scores,
                winner=winner,
                num_legs=num_legs,
                num_turns=num_turns,
                agent_names=agent_names,
                first_player=focal_seat,
            ))

    return NPlayerMatchupResult(
        focal_agent_name=focal_agent_name or "",
        field_agent_names=field_agent_names or (),
        num_players=n,
        games=tuple(games),
        base_seed=base_seed,
        fast_mode=False,
        elapsed_seconds=0.0,
    )
