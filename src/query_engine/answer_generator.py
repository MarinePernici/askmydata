from llm.base import LLMProvider
from llm.types import LLMMessage
from query_engine.types import (
    AnswerGenerationResult,
    QueryExecutionResult,
)


class AnswerGenerator:
    """Generate a natural-language answer from a query execution result."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate(
        self,
        question: str,
        sql: str,
        result: QueryExecutionResult,
    ) -> AnswerGenerationResult:
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You generate concise natural-language answers from SQL "
                    "query results.\n\n"
                    "Rules:\n"
                    "- Base the answer only on the provided query result.\n"
                    "- Do not invent facts that are not present in the result.\n"
                    "- If the result is empty, clearly state that no matching "
                    "data was found.\n"
                    "- Do not expose implementation details unless they are "
                    "needed to answer the question.\n\n"
                    f"SQL:\n{sql}\n\n"
                    f"Columns:\n{result.columns}\n\n"
                    f"Rows:\n{result.rows}"
                ),
            ),
            LLMMessage(
                role="user",
                content=question,
            ),
        ]

        response = self._provider.generate(messages)

        return AnswerGenerationResult(
            answer=response.content,
        )
