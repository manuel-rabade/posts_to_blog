"""Abstract base class for AI engines"""

from abc import ABC, abstractmethod

class EngineAI(ABC):
    def __init__(self, config):
        """
        Initializes the AI engine with the provided configuration.

        Args:
            config (dict): Configuration for the AI engine.
        """
        self.config = config

    @abstractmethod
    def setup(self):
        """
        Sets up the AI engine with necessary configurations.
        """
        pass

    @abstractmethod
    def generate(self, prompt, config):
        """
        Generates content based on the provided prompt and configuration.

        Args:
            prompt (str): Input text for the AI engine.
            config (dict): Additional parameters for generation.

        Returns:
            str: Generated content.
        """
        pass

    @abstractmethod
    def stats(self):
        """
        Outputs statistics about the engine's operation.
        """
        pass
