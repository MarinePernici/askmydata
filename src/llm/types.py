from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    """A message exchanged with a language model."""

    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """A response returned by a language model provider."""

    content: str
    model: str
