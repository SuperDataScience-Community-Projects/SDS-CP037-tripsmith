from abc import ABC, abstractmethod
from typing import Any, Dict


class Agent(ABC):
    """Abstract base for all agents."""

    name: str = "agent"

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the agent task.

        Args:
            **kwargs: Arbitrary keyword inputs for the agent.

        Returns:
            Dict[str, Any]: Structured payload defined by each agent.

        Raises:
            NotImplementedError: If not overridden by subclass.

        Notes:
            Each agent should return JSON-serializable content.
        """
        raise NotImplementedError
