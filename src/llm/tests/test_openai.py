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
            usage=SimpleNamespace(
                input_tokens=120,
                output_tokens=30,
            ),
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
        self.assertEqual(response.usage.model, "gpt-5-mini")
        self.assertEqual(response.usage.prompt_tokens, 120)
        self.assertEqual(response.usage.completion_tokens, 30)

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

    def test_generate_handles_missing_usage(self):
        client = FakeOpenAIClient()
        client.responses.create = lambda **kwargs: SimpleNamespace(
            output_text="SELECT 1;",
            model="gpt-5-mini",
            usage=None,
        )

        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-5-mini",
            client=client,
        )

        response = provider.generate(
            [
                LLMMessage(
                    role="user",
                    content="Test",
                )
            ]
        )

        self.assertEqual(response.usage.model, "gpt-5-mini")
        self.assertIsNone(response.usage.prompt_tokens)
        self.assertIsNone(response.usage.completion_tokens)
