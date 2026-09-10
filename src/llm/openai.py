from openai import OpenAI

from llm.base import LLMProvider
from llm.types import LLMMessage, LLMResponse


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        client: OpenAI | None = None,
    ) -> None:
        self._model = model
        self._client = client or OpenAI(api_key=api_key)

    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        """Generate a response using the configured OpenAI model."""
        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in messages
            ],
        )

        return LLMResponse(
            content=response.output_text,
            model=response.model,
        )