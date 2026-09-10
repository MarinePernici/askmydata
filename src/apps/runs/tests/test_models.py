from django.test import TestCase

from apps.projects.models import Project
from apps.runs.models import QuestionRun, ExecutionTrace


class QuestionRunModelTests(TestCase):
    def test_question_run_has_pending_status_by_default(self):
        project = Project.objects.create(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        self.assertEqual(
            run.status,
            QuestionRun.Status.PENDING,
        )

    def test_question_run_belongs_to_project(self):
        project = Project.objects.create(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        self.assertEqual(run.project, project)
        self.assertIn(run, project.question_runs.all())

    def test_execution_trace_belongs_to_question_run(self):
        project = Project.objects.create(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        trace = ExecutionTrace.objects.create(
            question_run=run,
            step="sql_generation",
        )

        self.assertEqual(trace.question_run, run)
        self.assertIn(trace, run.execution_traces.all())

    def test_execution_trace_has_pending_status_by_default(self):
        project = Project.objects.create(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        trace = ExecutionTrace.objects.create(
            question_run=run,
            step="sql_generation",
        )

        self.assertEqual(
            trace.status,
            ExecutionTrace.Status.PENDING,
        )