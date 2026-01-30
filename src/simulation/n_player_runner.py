"""N-player simulation runner for batch game execution."""

import time
from dataclasses import dataclass
from multiprocessing import Pool
from typing import List, Tuple

from src.game.game import play_game
from src.simulation.results import GameResult
from src.simulation.runner import AGENT_REGISTRY
from src.simulation.n_player_results import NPlayerMatchupResult


@dataclass(frozen=True)
class NPlayerGameConfig:
    """Configuration for a single N-player game in a simulation batch."""
    game_index: int
    seed: int
    agent_names: Tuple[str, ...]  # Ordered by seat
    focal_seat: int               # Which seat the focal agent occupies
    fast_mode: bool


def _run_single_n_player_game(config: NPlayerGameConfig) -> GameResult:
    """Run a single N-player game from a config. Module-level for multiprocessing."""
    n = len(config.agent_names)
    agents = []
    for seat in range(n):
        name = config.agent_names[seat]
        agent_seed = config.seed + seat * 10000
        agents.append(AGENT_REGISTRY[name](seed=agent_seed, fast_mode=config.fast_mode))

    final_state, history = play_game(
        num_players=n,
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
        agent_names=config.agent_names,
        first_player=config.focal_seat,
    )


class NPlayerRunner:
    """Runs batch N-player simulations with one focal agent vs a field."""

    def __init__(
        self,
        focal_agent_name: str,
        field_agent_names: Tuple[str, ...],
        num_games: int,
        base_seed: int = 0,
        fast_mode: bool = True,
        num_workers: int = 1,
        progress_interval: int = 100,
    ):
        all_names = [focal_agent_name] + list(field_agent_names)
        for name in all_names:
            if name not in AGENT_REGISTRY:
                raise ValueError(f"Unknown agent: {name}")

        self.focal_agent_name = focal_agent_name
        self.field_agent_names = field_agent_names
        self.num_players = 1 + len(field_agent_names)
        self.num_games = num_games
        self.base_seed = base_seed
        self.fast_mode = fast_mode
        self.num_workers = num_workers
        self.progress_interval = progress_interval

    def _make_configs(self) -> List[NPlayerGameConfig]:
        """Build game configs with seat rotation.

        Game i places the focal agent in seat (i % N). Field agents fill
        remaining seats in their original order.
        """
        configs = []
        n = self.num_players
        for i in range(self.num_games):
            focal_seat = i % n
            agent_names = []
            field_idx = 0
            for seat in range(n):
                if seat == focal_seat:
                    agent_names.append(self.focal_agent_name)
                else:
                    agent_names.append(self.field_agent_names[field_idx])
                    field_idx += 1
            configs.append(NPlayerGameConfig(
                game_index=i,
                seed=self.base_seed + i,
                agent_names=tuple(agent_names),
                focal_seat=focal_seat,
                fast_mode=self.fast_mode,
            ))
        return configs

    def run(self) -> NPlayerMatchupResult:
        """Run the simulation and return results."""
        configs = self._make_configs()
        start = time.time()

        if self.num_workers == 1:
            results = self._run_serial(configs)
        else:
            results = self._run_parallel(configs)

        results.sort(key=lambda r: r.game_index)
        elapsed = time.time() - start

        return NPlayerMatchupResult(
            focal_agent_name=self.focal_agent_name,
            field_agent_names=self.field_agent_names,
            num_players=self.num_players,
            games=tuple(results),
            base_seed=self.base_seed,
            fast_mode=self.fast_mode,
            elapsed_seconds=elapsed,
        )

    def _run_serial(self, configs: List[NPlayerGameConfig]) -> List[GameResult]:
        results = []
        for i, config in enumerate(configs):
            results.append(_run_single_n_player_game(config))
            if (i + 1) % self.progress_interval == 0:
                print(f"Progress: {i + 1}/{self.num_games} games complete", flush=True)
        return results

    def _run_parallel(self, configs: List[NPlayerGameConfig]) -> List[GameResult]:
        results = []
        with Pool(processes=self.num_workers) as pool:
            for i, result in enumerate(pool.imap_unordered(_run_single_n_player_game, configs)):
                results.append(result)
                if (i + 1) % self.progress_interval == 0:
                    print(f"Progress: {i + 1}/{self.num_games} games complete", flush=True)
        return results
