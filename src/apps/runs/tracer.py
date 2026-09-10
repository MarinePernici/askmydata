from apps.runs.models import ExecutionTrace, QuestionRun
from query_engine.tracer import QueryTracer


class DjangoQueryTracer(QueryTracer):
    """Persist query pipeline trace events using Django."""

    def __init__(self, question_run: QuestionRun) -> None:
        self._question_run = question_run

    def record(
        self,
        step: str,
        status: str,
        duration_ms: int,
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        ExecutionTrace.objects.create(
            question_run=self._question_run,
            step=step,
            status=status,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message,
        )