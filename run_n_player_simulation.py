"""N-player simulation: test skill decay as player count increases.

Hypothesis: GreedyAgent win rate decays toward 1/N baseline as N grows.
- 2-player: ~99% win rate (established in Phase 4)
- 4-player: ~40% expected
- 6-player: ~20% expected (barely above 16.7% baseline)

Runs GreedyAgent vs N-1 RandomAgents and N-1 HeuristicAgents for N=2,4,6.
"""

import os
from multiprocessing import cpu_count
from src.simulation.n_player_runner import NPlayerRunner
from src.simulation.n_player_results import save_n_player_results_csv
from src.simulation.n_player_analysis import summary_text

# (focal_agent, field_agent, num_players)
MATCHUPS = [
    # Greedy vs Random at increasing player counts
    ("GreedyAgent", "RandomAgent", 2),
    ("GreedyAgent", "RandomAgent", 4),
    ("GreedyAgent", "RandomAgent", 6),
    # Greedy vs Heuristic at increasing player counts
    ("GreedyAgent", "HeuristicAgent", 2),
    ("GreedyAgent", "HeuristicAgent", 4),
    ("GreedyAgent", "HeuristicAgent", 6),
]

NUM_GAMES = 1000
BASE_SEED = 0
FAST_MODE = True
NUM_WORKERS = cpu_count()
OUTPUT_DIR = "results"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for focal, field, num_players in MATCHUPS:
        field_agents = tuple(field for _ in range(num_players - 1))
        label = f"{focal} vs {num_players - 1}x {field} ({num_players}P)"

        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}\n")

        runner = NPlayerRunner(
            focal_agent_name=focal,
            field_agent_names=field_agents,
            num_games=NUM_GAMES,
            base_seed=BASE_SEED,
            fast_mode=FAST_MODE,
            num_workers=NUM_WORKERS,
            progress_interval=10,
        )
        result = runner.run()

        filename = f"{focal.lower()}_vs_{num_players - 1}x{field.lower()}_{num_players}p.csv"
        save_n_player_results_csv(result, os.path.join(OUTPUT_DIR, filename))
        print(summary_text(result))
        print()


if __name__ == "__main__":
    main()
