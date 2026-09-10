import unittest

from llm.base import LLMProvider


class IncompleteLLMProvider(LLMProvider):
    pass


class LLMProviderTests(unittest.TestCase):
    def test_provider_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            LLMProvider()

    def test_incomplete_provider_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            IncompleteLLMProvider()
