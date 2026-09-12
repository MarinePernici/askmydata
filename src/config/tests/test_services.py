from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.catalogs.readers import CatalogReader
from config.services import (
    create_catalog_service,
    create_llm_provider,
    create_question_run_service,
)
from apps.conversations.services import ConversationService
from query_engine.postgresql_executor import PostgreSQLQueryExecutor


class ServiceFactoryTests(SimpleTestCase):
    @override_settings(
        OPENAI_API_KEY="test-api-key",
        LLM_MODEL="test-model",
    )
    @patch("config.services.OpenAIProvider")
    def test_create_llm_provider_uses_django_settings(
        self,
        mock_provider,
    ):
        create_llm_provider()

        mock_provider.assert_called_once_with(
            api_key="test-api-key",
            model="test-model",
        )

    @patch("config.services.CatalogService")
    @patch("config.services.SemanticEnricher")
    @patch("config.services.create_llm_provider")
    def test_create_catalog_service_wires_dependencies(
        self,
        mock_create_llm_provider,
        mock_semantic_enricher,
        mock_catalog_service,
    ):
        provider = Mock()
        enricher = Mock()

        mock_create_llm_provider.return_value = provider
        mock_semantic_enricher.return_value = enricher

        create_catalog_service()

        mock_semantic_enricher.assert_called_once_with(
            provider=provider,
        )

        mock_catalog_service.assert_called_once_with(
            semantic_enricher=enricher,
        )

    @patch("config.services.QuestionRunService")
    @patch("config.services.ConversationService")
    @patch("config.services.CatalogReader")
    @patch("config.services.AnswerGenerator")
    @patch("config.services.ResultValidator")
    @patch("config.services.SQLValidator")
    @patch("config.services.SQLGenerator")
    @patch("config.services.create_llm_provider")
    def test_create_question_run_service_wires_dependencies(
        self,
        mock_create_llm_provider,
        mock_sql_generator,
        mock_sql_validator,
        mock_result_validator,
        mock_answer_generator,
        mock_catalog_reader,
        mock_conversation_service,
        mock_question_run_service,
    ):
        provider = object()
        generator = object()
        validator = object()
        result_validator = object()
        answer_generator = object()
        catalog_reader = object()
        conversation_service = object()

        mock_create_llm_provider.return_value = provider
        mock_sql_generator.return_value = generator
        mock_sql_validator.return_value = validator
        mock_result_validator.return_value = result_validator
        mock_answer_generator.return_value = answer_generator
        mock_catalog_reader.return_value = catalog_reader
        mock_conversation_service.return_value = conversation_service

        create_question_run_service()

        mock_sql_generator.assert_called_once_with(
            provider=provider,
        )

        mock_answer_generator.assert_called_once_with(
            provider=provider,
        )

        mock_catalog_reader.assert_called_once_with()

        mock_conversation_service.assert_called_once_with()

        mock_question_run_service.assert_called_once_with(
            generator=generator,
            validator=validator,
            executor_factory=PostgreSQLQueryExecutor,
            result_validator=result_validator,
            answer_generator=answer_generator,
            catalog_reader=catalog_reader,
            conversation_service=conversation_service,
        )