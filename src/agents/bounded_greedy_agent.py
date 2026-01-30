"""Greedy agent with depth-limited probability calculation."""

from .greedy_agent import GreedyAgent, OVERALL_BET_THRESHOLD


class BoundedGreedyAgent(GreedyAgent):
    """GreedyAgent with depth-limited probability calculation.

    Models human cognitive limits by only enumerating the next
    depth_limit dice outcomes instead of all remaining dice.
    Default depth_limit=2 (180 outcomes vs 29,160 for full).
    """

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        overall_bet_threshold: float = OVERALL_BET_THRESHOLD,
        fast_mode: bool = False,
        depth_limit: int = 2,
    ):
        super().__init__(
            name=name,
            seed=seed,
            overall_bet_threshold=overall_bet_threshold,
            fast_mode=fast_mode,
            depth_limit=depth_limit,
        )
