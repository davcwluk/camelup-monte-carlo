"""Base Agent interface for Camel Up."""

from abc import ABC, abstractmethod
from typing import List
import random

from ..game.game import GameState, Action


class Agent(ABC):
    """Abstract base class for Camel Up agents."""

    def __init__(self, name: str | None = None, seed: int | None = None):
        """
        Initialize the agent.

        Args:
            name: Optional name for the agent (defaults to class name)
            seed: Random seed for reproducibility
        """
        self.name = name or self.__class__.__name__
        self.rng = random.Random(seed)
        self.last_action_evs = None

    @abstractmethod
    def choose_action(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """
        Choose an action from the list of legal actions.

        Args:
            state: Current game state
            legal_actions: List of legal actions to choose from

        Returns:
            The chosen action
        """
        pass

    def __call__(
        self,
        state: GameState,
        legal_actions: List[Action]
    ) -> Action:
        """
        Make the agent callable for use with play_game().

        This allows agents to be used directly as agent_functions.
        """
        return self.choose_action(state, legal_actions)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
