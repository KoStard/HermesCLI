import unittest
from argparse import ArgumentParser
from unittest.mock import MagicMock, patch
from hermes.context_orchestrator import ContextOrchestrator
from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestContextOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_provider1 = MagicMock(spec=ContextProvider)
        self.mock_provider2 = MagicMock(spec=ContextProvider)
        self.orchestrator = ContextOrchestrator([self.mock_provider1, self.mock_provider2])

    def test_add_arguments(self):
        mock_parser = MagicMock(spec=ArgumentParser)
        self.orchestrator.add_arguments(mock_parser)
        self.mock_provider1.add_argument.assert_called_once_with(mock_parser)
        self.mock_provider2.add_argument.assert_called_once_with(mock_parser)

    def test_load_contexts(self):
        mock_args = MagicMock()
        self.orchestrator.load_contexts(mock_args)
        self.mock_provider1.load_context.assert_called_once_with(mock_args)
        self.mock_provider2.load_context.assert_called_once_with(mock_args)

    def test_build_prompt(self):
        mock_prompt_builder = MagicMock(spec=PromptBuilder)
        self.orchestrator.build_prompt(mock_prompt_builder)
        self.mock_provider1.add_to_prompt.assert_called_once_with(mock_prompt_builder)
        self.mock_provider2.add_to_prompt.assert_called_once_with(mock_prompt_builder)

if __name__ == '__main__':
    unittest.main()
