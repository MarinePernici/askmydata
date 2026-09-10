from django.utils import timezone

from apps.projects.models import Project
from apps.runs.models import QuestionRun
from apps.runs.tracer import DjangoQueryTracer
from catalog.types import KnowledgeCatalog
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import QueryRunResult


class QuestionRunService:
    def __init__(
        self,
        generator,
        validator,
        executor,
        result_validator,
        answer_generator,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._executor = executor
        self._result_validator = result_validator
        self._answer_generator = answer_generator

    def run(
        self,
        project: Project,
        question: str,
        catalog: KnowledgeCatalog,
    ) -> QueryRunResult:
        question_run = QuestionRun.objects.create(
            project=project,
            status=QuestionRun.Status.RUNNING,
            started_at=timezone.now(),
        )

        tracer = DjangoQueryTracer(
            question_run=question_run,
        )

        orchestrator = QueryOrchestrator(
            generator=self._generator,
            validator=self._validator,
            executor=self._executor,
            result_validator=self._result_validator,
            answer_generator=self._answer_generator,
            tracer=tracer,
        )

        try:
            result = orchestrator.run(
                question=question,
                catalog=catalog,
            )
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

        question_run.status = QuestionRun.Status.COMPLETED
        question_run.completed_at = timezone.now()
        question_run.row_count = len(result.execution.rows)
        question_run.save(
            update_fields=[
                "status",
                "completed_at",
                "row_count",
            ]
        )

        return result