from django.utils import timezone

from apps.conversations.models import Conversation, Message
from apps.projects.models import Project
from apps.runs.models import QuestionRun
from apps.runs.tracer import DjangoQueryTracer
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import ClarificationResult, QueryRunResult


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
    ) -> QueryRunResult:
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

        question_run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            user_message=user_message,
            status=QuestionRun.Status.RUNNING,
            started_at=timezone.now(),
        )

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
                question_run.completed_at = timezone.now()

                question_run.save(
                    update_fields=[
                        "assistant_message",
                        "status",
                        "completed_at",
                    ]
                )

                return result

        except Exception as exc:
            question_run.status = QuestionRun.Status.FAILED
            question_run.completed_at = timezone.now()
            question_run.error_code = exc.__class__.__name__
            question_run.error_message = str(exc)
            question_run.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_code",
                    "error_message",
                ]
            )
            raise

        assistant_message = self._conversation_service.add_message(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=result.answer,
        )

        question_run.assistant_message = assistant_message
        question_run.status = QuestionRun.Status.COMPLETED
        question_run.completed_at = timezone.now()
        question_run.row_count = len(result.execution.rows)
        question_run.save(
            update_fields=[
                "assistant_message",
                "status",
                "completed_at",
                "row_count",
            ]
        )

        return result