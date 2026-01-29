"""Phase 4 production simulation: all matchups, 1000 games each."""

import os
from multiprocessing import cpu_count
from src.simulation.runner import SimulationRunner
from src.simulation.results import save_results_csv
from src.simulation.analysis import summary_text

MATCHUPS = [
    ("RandomAgent",       "RandomAgent"),
    ("GreedyAgent",       "RandomAgent"),
    ("HeuristicAgent",    "RandomAgent"),
    ("ConservativeAgent", "RandomAgent"),
    ("GreedyAgent",       "HeuristicAgent"),
    ("GreedyAgent",       "ConservativeAgent"),
    ("GreedyAgent",       "GreedyAgent"),
]

NUM_GAMES = 1000
BASE_SEED = 0
FAST_MODE = False
NUM_WORKERS = cpu_count()
OUTPUT_DIR = "results"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for agent_a, agent_b in MATCHUPS:
        print(f"\n{'='*60}")
        print(f"  {agent_a} vs {agent_b}")
        print(f"{'='*60}\n")

        runner = SimulationRunner(
            agent_a_name=agent_a,
            agent_b_name=agent_b,
            num_games=NUM_GAMES,
            base_seed=BASE_SEED,
            fast_mode=FAST_MODE,
            num_workers=NUM_WORKERS,
            progress_interval=100,
        )
        result = runner.run()

        filename = f"{agent_a.lower()}_vs_{agent_b.lower()}.csv"
        save_results_csv(result, os.path.join(OUTPUT_DIR, filename))
        print(summary_text(result))
        print()


if __name__ == "__main__":
    main()
