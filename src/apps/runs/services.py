import logging

from django.utils import timezone

from apps.conversations.models import Conversation, Message
from apps.projects.models import Project
from apps.runs.error_messages import get_safe_error_message
from apps.runs.exceptions import ProjectNotReadyError
from apps.runs.models import QuestionRun
from apps.runs.tracer import DjangoQueryTracer
from config.observability import traced_question_run
from query_engine.exceptions import SQLValidationError
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import (
    CannotAnswerResult,
    ClarificationResult,
    QueryRunResult,
)

logger = logging.getLogger(__name__)


class QuestionRunService:
    def __init__(
        self,
        generator,
        validator,
        executor_factory,
        result_validator,
        answer_generator,
        catalog_reader,
        conversation_service,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._executor_factory = executor_factory
        self._result_validator = result_validator
        self._answer_generator = answer_generator
        self._catalog_reader = catalog_reader
        self._conversation_service = conversation_service

    def run(
        self,
        project: Project,
        conversation: Conversation,
        question: str,
    ) -> QueryRunResult | ClarificationResult | CannotAnswerResult:
        if project.status != Project.Status.READY:
            raise ProjectNotReadyError("Project is not ready.")

        if conversation.project_id != project.id:
            raise ValueError("Conversation does not belong to project.")

        history = self._conversation_service.get_history(
            conversation=conversation,
        )

        user_message = self._conversation_service.add_message(
            conversation=conversation,
            role=Message.Role.USER,
            content=question,
        )

        self._conversation_service.set_title_from_question(
            conversation=conversation,
            question=question,
        )

        question_run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            user_message=user_message,
            status=QuestionRun.Status.RUNNING,
            started_at=timezone.now(),
        )

        with traced_question_run(
            project_id=project.id,
            question_run_id=question_run.id,
        ):
            return self._execute_run(
                project=project,
                conversation=conversation,
                question=question,
                history=history,
                question_run=question_run,
            )

    def _execute_run(
        self,
        project: Project,
        conversation: Conversation,
        question: str,
        history,
        question_run: QuestionRun,
    ) -> QueryRunResult | ClarificationResult | CannotAnswerResult:
        try:
            catalog = self._catalog_reader.get_current(
                project=project,
            )

            config = project.data_source.to_connection_config()
            executor = self._executor_factory(config)

            tracer = DjangoQueryTracer(
                question_run=question_run,
            )

            orchestrator = QueryOrchestrator(
                generator=self._generator,
                validator=self._validator,
                executor=executor,
                result_validator=self._result_validator,
                answer_generator=self._answer_generator,
                tracer=tracer,
            )

            result = orchestrator.run(
                question=question,
                catalog=catalog,
                history=history,
            )

            if isinstance(result, ClarificationResult):
                assistant_message = self._conversation_service.add_message(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=result.question,
                )

                question_run.assistant_message = assistant_message
                question_run.status = QuestionRun.Status.NEEDS_CLARIFICATION
                self._apply_llm_usage(question_run, result.usages)
                self._complete_run_timing(question_run)

                question_run.save(
                    update_fields=[
                        "assistant_message",
                        "status",
                        "completed_at",
                        "latency_ms",
                        "model_name",
                        "prompt_tokens",
                        "completion_tokens",
                    ]
                )

                return result

            if isinstance(result, CannotAnswerResult):
                assistant_message = self._conversation_service.add_message(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=(
                        "I can't answer this question using the data available "
                        "in this project. Please ask a question related to the "
                        "project's data."
                    ),
                )

                question_run.assistant_message = assistant_message
                question_run.status = QuestionRun.Status.REJECTED
                self._apply_llm_usage(question_run, result.usages)
                self._complete_run_timing(question_run)

                question_run.save(
                    update_fields=[
                        "assistant_message",
                        "status",
                        "completed_at",
                        "latency_ms",
                        "model_name",
                        "prompt_tokens",
                        "completion_tokens",
                    ]
                )

                return result

        except SQLValidationError as exc:
            assistant_message = self._conversation_service.add_message(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=(
                    "I can't answer this question with the data available "
                    "in this project."
                ),
            )

            question_run.assistant_message = assistant_message
            question_run.status = QuestionRun.Status.FAILED
            self._complete_run_timing(question_run)
            question_run.error_code = exc.__class__.__name__
            question_run.error_message = str(exc)
            question_run.save(
                update_fields=[
                    "assistant_message",
                    "status",
                    "completed_at",
                    "latency_ms",
                    "error_code",
                    "error_message",
                ]
            )

            raise

        except Exception as exc:
            safe_message = get_safe_error_message(exc)

            assistant_message = self._conversation_service.add_message(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=safe_message,
            )

            question_run.assistant_message = assistant_message
            question_run.status = QuestionRun.Status.FAILED
            self._complete_run_timing(question_run)
            question_run.error_code = exc.__class__.__name__
            question_run.error_message = str(exc)

            question_run.save(
                update_fields=[
                    "assistant_message",
                    "status",
                    "completed_at",
                    "latency_ms",
                    "error_code",
                    "error_message",
                ]
            )

            logger.exception(
                "Unexpected failure while processing question run.",
                extra={
                    "event": "question_run.failed",
                    "project_id": project.id,
                    "question_run_id": question_run.id,
                },
            )
            raise

        assistant_message = self._conversation_service.add_message(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=result.answer,
        )

        question_run.assistant_message = assistant_message
        question_run.status = QuestionRun.Status.COMPLETED
        self._apply_llm_usage(question_run, result.usages)
        self._complete_run_timing(question_run)
        question_run.row_count = len(result.execution.rows)
        question_run.save(
            update_fields=[
                "assistant_message",
                "status",
                "completed_at",
                "latency_ms",
                "row_count",
                "model_name",
                "prompt_tokens",
                "completion_tokens",
            ]
        )

        return result

    @staticmethod
    def _complete_run_timing(question_run: QuestionRun) -> None:
        question_run.completed_at = timezone.now()
        question_run.latency_ms = int(
            (question_run.completed_at - question_run.started_at).total_seconds() * 1000
        )

    @staticmethod
    def _apply_llm_usage(question_run: QuestionRun, usages) -> None:
        if not usages:
            return

        question_run.model_name = usages[0].model

        prompt_tokens = [usage.prompt_tokens for usage in usages]
        completion_tokens = [usage.completion_tokens for usage in usages]

        if all(value is not None for value in prompt_tokens):
            question_run.prompt_tokens = sum(prompt_tokens)

        if all(value is not None for value in completion_tokens):
            question_run.completion_tokens = sum(completion_tokens)
