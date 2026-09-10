import os
import unittest

import environ

from catalog.builder import CatalogBuilder
from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)
from llm.base import LLMProvider
from llm.types import LLMMessage, LLMResponse
from query_engine.answer_generator import AnswerGenerator
from query_engine.orchestrator import QueryOrchestrator
from query_engine.postgresql_executor import PostgreSQLQueryExecutor
from query_engine.result_validator import ResultValidator
from query_engine.sql_generator import SQLGenerator
from query_engine.sql_validator import SQLValidator


ROOT_DIR = environ.Path(__file__) - 4
environ.Env.read_env(ROOT_DIR(".env"))


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
                model="fake-model",
            )

        return LLMResponse(
            content="The number of orders was successfully retrieved.",
            model="fake-model",
        )


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


if __name__ == "__main__":
    unittest.main()