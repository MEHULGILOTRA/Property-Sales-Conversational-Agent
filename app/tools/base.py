from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    All tools must implement this interface.
    LangGraph nodes depend on this abstraction.
    """

    @abstractmethod
    def run(self, state):
        pass
