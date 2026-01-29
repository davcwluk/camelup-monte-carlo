"""Random agent that picks uniformly from legal actions."""

from typing import List

from .base import Agent
from ..game.game import GameState, Action


class RandomAgent(Agent):
    """
    Agent that selects uniformly at random from all legal actions.

    Purpose: Baseline for comparison. Represents a player making
    decisions without any strategy.
    """

    def choose_action(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """Choose a random legal action."""
        return self.rng.choice(legal_actions)
