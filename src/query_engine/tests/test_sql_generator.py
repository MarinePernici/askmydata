import unittest

from catalog.types import KnowledgeCatalog, SemanticMetadata, TableMetadata
from connectors.types import ColumnMetadata
from llm.base import LLMProvider
from llm.types import LLMMessage, LLMResponse
from query_engine.exceptions import SQLGenerationError
from query_engine.sql_generator import SQLGenerator
from query_engine.types import (
    CannotAnswerResult,
    ClarificationResult,
    ConversationMessage,
)


class FakeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages: list[LLMMessage] = []

    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        self.messages = messages

        return LLMResponse(
            content=(
                '{"sql": "SELECT COUNT(*) FROM sales.orders;", '
                '"explanation": "Counts all orders."}'
            ),
            model="fake-model",
        )


class InvalidJSONProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        return LLMResponse(
            content="not-json",
            model="fake-model",
        )


class MissingFieldProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        return LLMResponse(
            content='{"sql": "SELECT 1;"}',
            model="fake-model",
        )


class ClarificationProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        return LLMResponse(
            content=('{"clarification": "Which date range should I use?"}'),
            model="fake-model",
        )


class EmptyClarificationProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        return LLMResponse(
            content='{"clarification": "   "}',
            model="fake-model",
        )


class CannotAnswerProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        return LLMResponse(
            content='{"cannot_answer": true}',
            model="fake-model",
        )


class SQLGeneratorTests(unittest.TestCase):
    def test_generator_can_be_created_with_llm_provider(self):
        provider = FakeLLMProvider()

        generator = SQLGenerator(provider)

        self.assertIsNotNone(generator)

    def test_generate_returns_structured_sql_result(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        catalog = KnowledgeCatalog(tables=())

        result = generator.generate(
            question="How many orders are there?",
            catalog=catalog,
        )

        self.assertEqual(
            result.sql,
            "SELECT COUNT(*) FROM sales.orders;",
        )
        self.assertEqual(
            result.explanation,
            "Counts all orders.",
        )

    def test_generate_sends_catalog_and_question_to_provider(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="bigint",
                            nullable=False,
                            default=None,
                        ),
                    ),
                    relationships=(),
                ),
            )
        )

        generator.generate(
            question="How many orders are there?",
            catalog=catalog,
        )

        self.assertEqual(len(provider.messages), 2)

        system_message = provider.messages[0]
        user_message = provider.messages[1]

        self.assertEqual(system_message.role, "system")
        self.assertIn("TABLE sales.orders", system_message.content)
        self.assertIn("COLUMN id bigint NOT NULL", system_message.content)

        self.assertEqual(user_message.role, "user")
        self.assertEqual(
            user_message.content,
            "How many orders are there?",
        )

    def test_generate_raises_error_for_invalid_json(self):
        provider = InvalidJSONProvider()
        generator = SQLGenerator(provider)

        with self.assertRaises(SQLGenerationError):
            generator.generate(
                question="How many orders are there?",
                catalog=KnowledgeCatalog(tables=()),
            )

    def test_generate_raises_error_for_missing_fields(self):
        provider = MissingFieldProvider()
        generator = SQLGenerator(provider)

        with self.assertRaises(SQLGenerationError):
            generator.generate(
                question="Test",
                catalog=KnowledgeCatalog(tables=()),
            )

    def test_generate_sends_semantic_metadata_to_provider(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders",
                        business_synonyms=(
                            "sales orders",
                            "purchases",
                        ),
                    ),
                ),
            )
        )

        generator.generate(
            question="How many purchases are there?",
            catalog=catalog,
        )

        system_message = provider.messages[0]

        self.assertIn(
            "DESCRIPTION Customer orders",
            system_message.content,
        )
        self.assertIn(
            "SYNONYMS sales orders, purchases",
            system_message.content,
        )

    def test_generate_includes_conversation_history_in_system_prompt(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        history = (
            ConversationMessage(
                role="user",
                content="How many orders are there?",
            ),
            ConversationMessage(
                role="assistant",
                content="There are 42 orders.",
            ),
        )

        generator.generate(
            question="And how many this month?",
            catalog=KnowledgeCatalog(tables=()),
            history=history,
        )

        system_message = provider.messages[0]
        user_message = provider.messages[1]

        self.assertIn(
            "user: How many orders are there?",
            system_message.content,
        )
        self.assertIn(
            "assistant: There are 42 orders.",
            system_message.content,
        )

        self.assertEqual(
            user_message.content,
            "And how many this month?",
        )

    def test_generate_handles_empty_conversation_history(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        generator.generate(
            question="How many orders are there?",
            catalog=KnowledgeCatalog(tables=()),
        )

        system_message = provider.messages[0]

        self.assertIn(
            "No previous conversation.",
            system_message.content,
        )

    def test_generate_returns_clarification_when_question_is_ambiguous(self):
        provider = ClarificationProvider()
        generator = SQLGenerator(provider)

        result = generator.generate(
            question="How many recent orders are there?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(
            result,
            ClarificationResult(
                question="Which date range should I use?",
            ),
        )

    def test_generate_returns_cannot_answer_when_question_is_out_of_scope(self):
        provider = CannotAnswerProvider()
        generator = SQLGenerator(provider)

        result = generator.generate(
            question="What is the capital of Italy?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(
            result,
            CannotAnswerResult(),
        )

    def test_generate_instructs_model_to_reject_unanswerable_questions(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        generator.generate(
            question="What is the capital of Italy?",
            catalog=KnowledgeCatalog(tables=()),
        )

        system_message = provider.messages[0]

        self.assertIn(
            "not represented in or derivable from the catalog",
            system_message.content,
        )
        self.assertIn(
            "do not use external knowledge",
            system_message.content,
        )
        self.assertIn(
            '"cannot_answer"',
            system_message.content,
        )

    def test_generate_rejects_empty_clarification(self):
        provider = EmptyClarificationProvider()
        generator = SQLGenerator(provider)

        with self.assertRaises(SQLGenerationError):
            generator.generate(
                question="How many recent orders are there?",
                catalog=KnowledgeCatalog(tables=()),
            )

    def test_generate_instructs_model_to_clarify_ambiguous_questions(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        generator.generate(
            question="Which customers are the best?",
            catalog=KnowledgeCatalog(tables=()),
        )

        system_message = provider.messages[0]

        self.assertIn(
            "different reasonable interpretations",
            system_message.content,
        )
        self.assertIn(
            '"clarification"',
            system_message.content,
        )

    def test_generate_instructs_model_to_preserve_question_constraints(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        generator.generate(
            question="Which customers have the highest total payments?",
            catalog=KnowledgeCatalog(tables=()),
        )

        system_message = provider.messages[0]

        self.assertIn(
            "Preserve explicit constraints",
            system_message.content,
        )
        self.assertIn(
            "singular/plural intent",
            system_message.content,
        )
        self.assertIn(
            "multiple ranked results",
            system_message.content,
        )

    def test_generate_instructs_model_not_to_invent_business_semantics(self):
        provider = FakeLLMProvider()
        generator = SQLGenerator(provider)

        generator.generate(
            question="What is the profit generated by each film category?",
            catalog=KnowledgeCatalog(tables=()),
        )

        system_message = provider.messages[0]

        self.assertIn(
            "Do not invent or assume business definitions",
            system_message.content,
        )
        self.assertIn(
            "cannot be derived from the catalog",
            system_message.content,
        )
        self.assertIn(
            "Never suggest candidate formulas",
            system_message.content,
        )
        self.assertIn(
            "without giving formula examples",
            system_message.content,
        )
