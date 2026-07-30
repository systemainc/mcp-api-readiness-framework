from abc import ABC, abstractmethod


class LegibilityProvider(ABC):
    @abstractmethod
    def assess(self, prompt: str) -> str:
        """Return a short assessment string, plain text, no markdown."""
