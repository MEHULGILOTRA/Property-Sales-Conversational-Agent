from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    All tools must implement this interface.
    LangGraph nodes depend on this abstraction.
    """

    @abstractmethod
    def run(self, state):
        pass
