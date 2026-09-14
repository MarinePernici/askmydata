import unittest
from types import SimpleNamespace

from llm.openai import OpenAIProvider
from llm.types import LLMMessage


class FakeResponses:
    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs

        return SimpleNamespace(
            output_text="SELECT COUNT(*) FROM sales.orders;",
            model="gpt-5-mini",
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


class OpenAIProviderTests(unittest.TestCase):
    def test_generate_returns_llm_response(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-5-mini",
            client=FakeOpenAIClient(),
        )

        response = provider.generate(
            [
                LLMMessage(
                    role="user",
                    content="How many orders are there?",
                )
            ]
        )

        self.assertEqual(
            response.content,
            "SELECT COUNT(*) FROM sales.orders;",
        )
        self.assertEqual(response.model, "gpt-5-mini")

    def test_generate_sends_messages_and_model_to_openai(self):
        client = FakeOpenAIClient()

        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-5-mini",
            client=client,
        )

        provider.generate(
            [
                LLMMessage(
                    role="system",
                    content="Generate read-only PostgreSQL.",
                ),
                LLMMessage(
                    role="user",
                    content="How many orders are there?",
                ),
            ]
        )

        self.assertEqual(
            client.responses.last_request,
            {
                "model": "gpt-5-mini",
                "input": [
                    {
                        "role": "system",
                        "content": "Generate read-only PostgreSQL.",
                    },
                    {
                        "role": "user",
                        "content": "How many orders are there?",
                    },
                ],
            },
        )
