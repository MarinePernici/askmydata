import unittest

from llm.base import LLMProvider
from llm.types import LLMMessage, LLMResponse
from query_engine.answer_generator import AnswerGenerator
from query_engine.types import QueryExecutionResult


class FakeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages: list[LLMMessage] = []

    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        self.messages = messages

        return LLMResponse(
            content="There are 42 orders.",
            model="fake-model",
        )


class AnswerGeneratorTests(unittest.TestCase):
    def test_generator_can_be_created_with_llm_provider(self):
        provider = FakeLLMProvider()

        generator = AnswerGenerator(provider)

        self.assertIsNotNone(generator)

    def test_generate_returns_natural_language_answer(self):
        provider = FakeLLMProvider()
        generator = AnswerGenerator(provider)

        result = generator.generate(
            question="How many orders are there?",
            sql="SELECT COUNT(*) AS order_count FROM sales.orders;",
            result=QueryExecutionResult(
                columns=("order_count",),
                rows=((42,),),
            ),
        )

        self.assertEqual(
            result.answer,
            "There are 42 orders.",
        )

    def test_generate_sends_question_sql_and_result_to_provider(self):
        provider = FakeLLMProvider()
        generator = AnswerGenerator(provider)

        generator.generate(
            question="How many orders are there?",
            sql="SELECT COUNT(*) AS order_count FROM sales.orders;",
            result=QueryExecutionResult(
                columns=("order_count",),
                rows=((42,),),
            ),
        )

        self.assertEqual(len(provider.messages), 2)

        system_message = provider.messages[0]
        user_message = provider.messages[1]

        self.assertEqual(system_message.role, "system")
        self.assertIn(
            "SELECT COUNT(*) AS order_count FROM sales.orders;",
            system_message.content,
        )
        self.assertIn("order_count", system_message.content)
        self.assertIn("42", system_message.content)

        self.assertEqual(user_message.role, "user")
        self.assertEqual(
            user_message.content,
            "How many orders are there?",
        )


if __name__ == "__main__":
    unittest.main()
