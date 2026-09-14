import unittest

from query_engine.query_executor import QueryExecutor


class QueryExecutorTests(unittest.TestCase):
    def test_executor_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            QueryExecutor()

    def test_incomplete_executor_cannot_be_instantiated(self):
        class IncompleteExecutor(QueryExecutor):
            pass

        with self.assertRaises(TypeError):
            IncompleteExecutor()
