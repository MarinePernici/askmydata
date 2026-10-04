import os
import unittest

import environ

from catalog.builder import CatalogBuilder
from catalog.types import CatalogScope, CatalogTableSelection
from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)
from llm.base import LLMProvider
from llm.types import LLMMessage, LLMResponse, LLMUsage
from query_engine.answer_generator import AnswerGenerator
from query_engine.exceptions import SQLValidationError
from query_engine.orchestrator import QueryOrchestrator
from query_engine.postgresql_executor import PostgreSQLQueryExecutor
from query_engine.result_validator import ResultValidator
from query_engine.sql_generator import SQLGenerator
from query_engine.sql_validator import SQLValidator

ROOT_DIR = environ.Path(__file__) - 4
environ.Env.read_env(ROOT_DIR(".env"))

SQL_USAGE = LLMUsage(
    model="fake-model",
    prompt_tokens=100,
    completion_tokens=20,
)

ANSWER_USAGE = LLMUsage(
    model="fake-model",
    prompt_tokens=50,
    completion_tokens=10,
)


class FakeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.call_count = 0

    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        self.call_count += 1

        if self.call_count == 1:
            return LLMResponse(
                content=(
                    '{"sql": "SELECT COUNT(*) AS order_count '
                    'FROM sales.orders;", '
                    '"explanation": "Counts all orders."}'
                ),
                usage=SQL_USAGE,
            )

        return LLMResponse(
            content="The number of orders was successfully retrieved.",
            usage=ANSWER_USAGE,
        )


class OutOfScopeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.call_count = 0

    def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        self.call_count += 1

        return LLMResponse(
            content=(
                '{"sql": "SELECT COUNT(*) AS order_count '
                'FROM sales.orders;", '
                '"explanation": "Counts all orders."}'
            ),
            usage=SQL_USAGE,
        )


class RecordingExecutor:
    def __init__(self) -> None:
        self.called = False

    def execute(self, sql):
        self.called = True
        raise AssertionError("Out-of-scope SQL must not be executed.")


class QueryPipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.config = PostgreSQLConnectionConfig(
            host=os.environ["TEST_SOURCE_DB_HOST"],
            port=int(os.environ["TEST_SOURCE_DB_PORT"]),
            database=os.environ["TEST_SOURCE_DB_NAME"],
            user=os.environ["TEST_SOURCE_DB_USER"],
            password=os.environ["TEST_SOURCE_DB_PASSWORD"],
        )

    def test_complete_query_pipeline(self):
        connector = PostgreSQLConnector(self.config)
        catalog = CatalogBuilder(connector).build()

        provider = FakeLLMProvider()

        orchestrator = QueryOrchestrator(
            generator=SQLGenerator(provider),
            validator=SQLValidator(),
            executor=PostgreSQLQueryExecutor(self.config),
            result_validator=ResultValidator(),
            answer_generator=AnswerGenerator(provider),
        )

        result = orchestrator.run(
            question="How many orders are there?",
            catalog=catalog,
        )

        self.assertEqual(
            result.sql,
            "SELECT COUNT(*) AS order_count FROM sales.orders;",
        )
        self.assertEqual(
            result.explanation,
            "Counts all orders.",
        )
        self.assertEqual(
            result.execution.columns,
            ("order_count",),
        )
        self.assertEqual(
            len(result.execution.rows),
            1,
        )
        self.assertEqual(
            result.answer,
            "The number of orders was successfully retrieved.",
        )

        self.assertEqual(provider.call_count, 2)
        self.assertEqual(
            result.usages,
            (SQL_USAGE, ANSWER_USAGE),
        )

    def test_pipeline_rejects_query_outside_catalog_scope(self):
        connector = PostgreSQLConnector(self.config)

        catalog = CatalogBuilder(connector).build(
            scope=CatalogScope(
                tables=(
                    CatalogTableSelection(
                        schema="sales",
                        table="customers",
                    ),
                )
            )
        )

        provider = OutOfScopeLLMProvider()

        executor = RecordingExecutor()

        orchestrator = QueryOrchestrator(
            generator=SQLGenerator(provider),
            validator=SQLValidator(),
            executor=executor,
            result_validator=ResultValidator(),
            answer_generator=AnswerGenerator(provider),
        )

        with self.assertRaises(SQLValidationError):
            orchestrator.run(
                question="How many orders are there?",
                catalog=catalog,
            )

        self.assertEqual(provider.call_count, 1)
        self.assertFalse(executor.called)


if __name__ == "__main__":
    unittest.main()
