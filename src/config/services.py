from django.conf import settings

from apps.catalogs.readers import CatalogReader
from apps.catalogs.services import CatalogService
from apps.conversations.services import ConversationService
from apps.runs.services import QuestionRunService
from catalog.semantic_enricher import SemanticEnricher
from llm.openai import OpenAIProvider
from query_engine.answer_generator import AnswerGenerator
from query_engine.postgresql_executor import PostgreSQLQueryExecutor
from query_engine.result_validator import ResultValidator
from query_engine.sql_generator import SQLGenerator
from query_engine.sql_validator import SQLValidator


def create_llm_provider() -> OpenAIProvider:
    return OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model=settings.LLM_MODEL,
    )


def create_catalog_service() -> CatalogService:
    provider = create_llm_provider()

    semantic_enricher = SemanticEnricher(
        provider=provider,
    )

    return CatalogService(
        semantic_enricher=semantic_enricher,
    )


def create_question_run_service() -> QuestionRunService:
    provider = create_llm_provider()

    return QuestionRunService(
        generator=SQLGenerator(
            provider=provider,
        ),
        validator=SQLValidator(),
        executor_factory=PostgreSQLQueryExecutor,
        result_validator=ResultValidator(),
        answer_generator=AnswerGenerator(
            provider=provider,
        ),
        catalog_reader=CatalogReader(),
        conversation_service=ConversationService(),
    )
