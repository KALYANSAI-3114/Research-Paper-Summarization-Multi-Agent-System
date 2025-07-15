# agents/base_agent.py

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides a common interface and can define shared functionalities.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Abstract method to be implemented by concrete agents.
        Defines the main execution logic for the agent.
        """
        pass

    def __str__(self):
        return f"Agent: {self.name}"