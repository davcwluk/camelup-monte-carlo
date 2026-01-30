"""Simulation runner for batch game execution."""

import time
from dataclasses import dataclass
from multiprocessing import Pool
from typing import List

from src.agents import RandomAgent, GreedyAgent, BoundedGreedyAgent, HeuristicAgent, ConservativeAgent
from src.game.game import play_game
from src.simulation.results import GameResult, MatchupResult


# Agent registry: string names -> constructors.
# Avoids pickling issues -- agents are constructed fresh in each worker.
AGENT_REGISTRY = {
    "RandomAgent": lambda seed, fast_mode: RandomAgent(seed=seed),
    "GreedyAgent": lambda seed, fast_mode: GreedyAgent(seed=seed, fast_mode=fast_mode),
    "BoundedGreedyAgent": lambda seed, fast_mode: BoundedGreedyAgent(seed=seed, fast_mode=fast_mode),
    "HeuristicAgent": lambda seed, fast_mode: HeuristicAgent(seed=seed, fast_mode=fast_mode),
    "ConservativeAgent": lambda seed, fast_mode: ConservativeAgent(seed=seed, fast_mode=fast_mode),
}


@dataclass(frozen=True)
class GameConfig:
    """Configuration for a single game in a simulation batch."""
    game_index: int
    seed: int
    agent_a_name: str
    agent_b_name: str
    fast_mode: bool


def _run_single_game(config: GameConfig) -> GameResult:
    """Run a single game from a config. Module-level for multiprocessing."""
    # Even game_index -> agent A is seat 0 (goes first)
    # Odd game_index -> agent B is seat 0 (goes first)
    a_first = config.game_index % 2 == 0

    if a_first:
        seat_0_name = config.agent_a_name
        seat_1_name = config.agent_b_name
        first_player = 0
    else:
        seat_0_name = config.agent_b_name
        seat_1_name = config.agent_a_name
        first_player = 1

    agent_0 = AGENT_REGISTRY[seat_0_name](seed=config.seed, fast_mode=config.fast_mode)
    agent_1 = AGENT_REGISTRY[seat_1_name](seed=config.seed + 10000, fast_mode=config.fast_mode)

    agents = [agent_0, agent_1]
    final_state, history = play_game(
        num_players=2,
        agent_functions=agents,
        seed=config.seed,
    )

    scores = final_state.get_scores()
    winner = final_state.get_winner()

    return GameResult(
        game_index=config.game_index,
        seed=config.seed,
        scores=scores,
        winner=winner,
        num_legs=final_state.leg_number,
        num_turns=len(history),
        agent_names=(seat_0_name, seat_1_name),
        first_player=first_player,
    )


class SimulationRunner:
    """Runs batch simulations between two agents."""

    def __init__(
        self,
        agent_a_name: str,
        agent_b_name: str,
        num_games: int,
        base_seed: int = 0,
        fast_mode: bool = True,
        num_workers: int = 1,
        progress_interval: int = 100,
    ):
        if agent_a_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_a_name}")
        if agent_b_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_b_name}")

        self.agent_a_name = agent_a_name
        self.agent_b_name = agent_b_name
        self.num_games = num_games
        self.base_seed = base_seed
        self.fast_mode = fast_mode
        self.num_workers = num_workers
        self.progress_interval = progress_interval

    def _make_configs(self) -> List[GameConfig]:
        return [
            GameConfig(
                game_index=i,
                seed=self.base_seed + i,
                agent_a_name=self.agent_a_name,
                agent_b_name=self.agent_b_name,
                fast_mode=self.fast_mode,
            )
            for i in range(self.num_games)
        ]

    def run(self) -> MatchupResult:
        """Run the simulation and return results."""
        configs = self._make_configs()
        start = time.time()

        if self.num_workers == 1:
            results = self._run_serial(configs)
        else:
            results = self._run_parallel(configs)

        # Sort by game_index for deterministic output
        results.sort(key=lambda r: r.game_index)
        elapsed = time.time() - start

        return MatchupResult(
            agent_a_name=self.agent_a_name,
            agent_b_name=self.agent_b_name,
            games=tuple(results),
            base_seed=self.base_seed,
            fast_mode=self.fast_mode,
            elapsed_seconds=elapsed,
        )

    def _run_serial(self, configs: List[GameConfig]) -> List[GameResult]:
        results = []
        for i, config in enumerate(configs):
            results.append(_run_single_game(config))
            if (i + 1) % self.progress_interval == 0:
                print(f"Progress: {i + 1}/{self.num_games} games complete", flush=True)
        return results

    def _run_parallel(self, configs: List[GameConfig]) -> List[GameResult]:
        results = []
        with Pool(processes=self.num_workers) as pool:
            for i, result in enumerate(pool.imap_unordered(_run_single_game, configs)):
                results.append(result)
                if (i + 1) % self.progress_interval == 0:
                    print(f"Progress: {i + 1}/{self.num_games} games complete", flush=True)
        return results
