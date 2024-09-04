import unittest
from unittest.mock import Mock, patch
import yaml
from hermes.prompt_builders.base import PromptBuilder
from hermes.workflows.context import WorkflowContext
from hermes.workflows.executor import WorkflowExecutor
from hermes.workflows.parser import WorkflowParser
from hermes.chat_models.base import ChatModel
from hermes.workflows.tasks.base import Task

class TestWorkflowContext(unittest.TestCase):
    def setUp(self):
        self.context = WorkflowContext()

    def test_set_get_global(self):
        self.context.set_global('key', 'value')
        self.assertEqual(self.context.get_global('key'), 'value')
        self.assertIsNone(self.context.get_global('nonexistent'))
        self.assertEqual(self.context.get_global('nonexistent', 'default'), 'default')

    def test_set_get_task_context(self):
        self.context.set_task_context('task1', 'key', 'value')
        self.assertEqual(self.context.get_task_context('task1', 'key'), 'value')
        self.assertIsNone(self.context.get_task_context('task1', 'nonexistent'))
        self.assertEqual(self.context.get_task_context('task1', 'nonexistent', 'default'), 'default')
        self.assertIsNone(self.context.get_task_context('nonexistent_task', 'key'))

    def test_clear_task_context(self):
        self.context.set_task_context('task1', 'key', 'value')
        self.context.clear_task_context('task1')
        self.assertIsNone(self.context.get_task_context('task1', 'key'))

    def test_clear_all(self):
        self.context.set_global('global_key', 'global_value')
        self.context.set_task_context('task1', 'task_key', 'task_value')
        self.context.clear_all()
        self.assertIsNone(self.context.get_global('global_key'))
        self.assertIsNone(self.context.get_task_context('task1', 'task_key'))

    def test_copy(self):
        self.context.set_global('global_key', 'global_value')
        self.context.set_task_context('task1', 'task_key', 'task_value')
        copied_context = self.context.copy()
        self.assertEqual(copied_context.get_global('global_key'), 'global_value')
        self.assertEqual(copied_context.get_task_context('task1', 'task_key'), 'task_value')

        # Ensure changes to the copy don't affect the original
        copied_context.set_global('new_key', 'new_value')
        self.assertIsNone(self.context.get_global('new_key'))

class TestWorkflowParser(unittest.TestCase):
    def setUp(self):
        self.model_mock = Mock(spec=ChatModel)
        self.printer_mock = Mock()
        self.parser = WorkflowParser(self.model_mock, self.printer_mock)

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="task1:\n  type: llm\n  prompt: test")
    def test_parse_valid_workflow(self, mock_open):
        result = self.parser.parse('dummy_file.yaml')
        self.assertIsInstance(result, Task)
        self.assertEqual(result.task_id, 'task1')
        self.assertEqual(result.task_config['type'], 'llm')
        self.assertEqual(result.task_config['prompt'], 'test')

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="invalid_yaml:")
    def test_parse_invalid_yaml(self, mock_open):
        with self.assertRaises(ValueError):
            self.parser.parse('dummy_file.yaml')

    def test_parse_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse('nonexistent_file.yaml')

    def test_validate_workflow(self):
        valid_workflow = {'task1': {'type': 'llm'}}
        self.assertTrue(self.parser.validate_workflow(valid_workflow))

        invalid_workflow1 = {'task1': {'no_type': 'llm'}}
        self.assertFalse(self.parser.validate_workflow(invalid_workflow1))

        invalid_workflow2 = {'task1': {'type': 'llm'}, 'task2': {'type': 'shell'}}
        self.assertFalse(self.parser.validate_workflow(invalid_workflow2))

class TestWorkflowExecutor(unittest.TestCase):
    @patch('hermes.workflows.parser.WorkflowParser')
    def setUp(self, MockParser):
        self.model_mock = Mock(spec=ChatModel)
        self.prompt_builder_mock = Mock(spec=PromptBuilder)
        self.root_task_mock = Mock(spec=Task, task_id="test_task")

        self.mock_parser = MockParser.return_value
        self.mock_parser.parse.return_value = self.root_task_mock

        with patch('builtins.open', unittest.mock.mock_open(read_data="task1:\n  type: llm\n  prompt: test")):
            self.executor = WorkflowExecutor(
                'dummy_workflow.yaml',
                self.model_mock,
                self.prompt_builder_mock,
                ['input1.txt', 'input2.txt'],
                'initial prompt',
                print
            )

    def test_initialization(self):
        self.assertEqual(self.executor.context.get_global('input_files'), ['input1.txt', 'input2.txt'])
        self.assertEqual(self.executor.context.get_global('initial_prompt'), 'initial prompt')
        self.assertEqual(self.executor.context.get_global('prompt_builder'), self.prompt_builder_mock)

    def test_execute(self):
        self.root_task_mock.execute.return_value = {'result': 'task_result'}
        self.model_mock.send_message.return_value = iter(['chunk1', 'chunk2'])

        result = self.executor.execute()

        self.model_mock.initialize.assert_called_once()
        self.root_task_mock.execute.assert_called_once_with(self.executor.context)
        self.assertEqual(result, {'result': 'task_result'})
        self.assertEqual(self.executor.context.get_task_context(self.root_task_mock.task_id, 'result'), 'task_result')

if __name__ == '__main__':
    unittest.main()
