from abc import ABC, abstractmethod

from llm.types import LLMMessage, LLMResponse


class LLMProvider(ABC):
    """Abstract interface for interacting with a language model."""

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        """Generate a response from a sequence of messages."""
        raise NotImplementedError