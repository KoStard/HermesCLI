import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile

from hermes.workflows.context import WorkflowContext
from hermes.workflows.tasks.base import Task
from hermes.workflows.tasks.markdown_extraction_task import MarkdownExtractionTask
from hermes.workflows.tasks.sequential_task import SequentialTask
from hermes.workflows.tasks.llm_task import LLMTask
from hermes.workflows.tasks.shell_task import ShellTask
from hermes.workflows.tasks.context_extension_task import ContextExtensionTask
from hermes.workflows.tasks.chat_application_task import ChatApplicationTask
from hermes.workflows.tasks.map_task import MapTask
from hermes.workflows.tasks.if_else_task import IfElseTask
from hermes.chat_models.base import ChatModel
from hermes.chat_application import ChatApplication

class MockTask(Task):
    def execute(self, context: WorkflowContext) -> dict:
        return {"result": "mock_result"}

class TestBaseTask(unittest.TestCase):
    def test_base_task_initialization(self):
        task = MockTask("test_task", {"print_output": True}, print)
        self.assertEqual(task.task_id, "test_task")
        self.assertTrue(task.print_output)
        self.assertEqual(task.printer, print)

    def test_get_config(self):
        task = MockTask("test_task", {"key": "value"}, print)
        self.assertEqual(task.get_config("key"), "value")
        self.assertIsNone(task.get_config("nonexistent_key"))
        self.assertEqual(task.get_config("nonexistent_key", "default"), "default")

class TestMarkdownExtractionTask(unittest.TestCase):
    def setUp(self):
        self.task = MarkdownExtractionTask("md_extract", {"file_path_var": "input_file"}, print)

    def test_execute_pdf(self):
        context = WorkflowContext()
        context.set_global("input_file", "test.pdf")

        with patch("hermes.workflows.tasks.markdown_extraction_task.extract_pages") as mock_extract:
            mock_extract.return_value = [MagicMock()]
            result = self.task.execute(context)

        self.assertIn("extracted_text", result)
        self.assertIn("--- Content from test.pdf ---", result["extracted_text"])

    def test_execute_unsupported_file(self):
        context = WorkflowContext()
        context.set_global("input_file", "test.txt")

        with self.assertRaises(ValueError):
            self.task.execute(context)

class TestSequentialTask(unittest.TestCase):
    def setUp(self):
        self.sub_task1 = MockTask("sub_task1", {}, print)
        self.sub_task2 = MockTask("sub_task2", {}, print)
        self.task = SequentialTask("sequential", {}, [self.sub_task1, self.sub_task2], print)

    def test_execute(self):
        context = WorkflowContext()
        self.sub_task1.execute = MagicMock(return_value={"result1": "value1"})
        self.sub_task2.execute = MagicMock(return_value={"result2": "value2"})

        result = self.task.execute(context)

        self.sub_task1.execute.assert_called_once()
        self.sub_task2.execute.assert_called_once()
        self.assertIn("result1", result["sub_task1"])
        self.assertIn("result2", result["sub_task2"])
        self.assertIn("_debug", result)

class TestLLMTask(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock(spec=ChatModel)
        self.task = LLMTask("llm", {"prompt": "Test prompt", "pass_input_files": True}, self.model, print)

    def test_execute(self):
        context = WorkflowContext()
        context.set_global("input_files", ["file1.txt", "file2.txt"])
        context.set_global("prompt_formatter", MagicMock())

        self.model.send_message.return_value = iter(["Response"])

        result = self.task.execute(context)

        self.assertIn("response", result)
        self.assertEqual(result["response"], "Response")
        self.model.send_message.assert_called_once()

class TestShellTask(unittest.TestCase):
    def setUp(self):
        self.task = ShellTask("shell", {"command": "echo 'Hello, World!'"}, print)

    @patch("subprocess.run")
    def test_execute(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Hello, World!", stderr="", returncode=0)
        context = WorkflowContext()

        result = self.task.execute(context)

        self.assertEqual(result["stdout"], "Hello, World!")
        self.assertEqual(result["returncode"], 0)
        mock_run.assert_called_once_with("echo 'Hello, World!'", shell=True, check=True, capture_output=True, text=True)

class TestContextExtensionTask(unittest.TestCase):
    def setUp(self):
        self.task = ContextExtensionTask("context_extension", {"files": ["file1.txt", "file2.txt"]}, print, "/workflow/dir")

    def test_execute(self):
        context = WorkflowContext()
        context.set_global("input_files", ["existing.txt"])

        result = self.task.execute(context)

        self.assertIn("extended_files", result)
        self.assertIn("processed_files", result)
        self.assertEqual(len(result["extended_files"]), 3)
        self.assertEqual(len(result["processed_files"]), 3)

class TestChatApplicationTask(unittest.TestCase):
    def setUp(self):
        self.chat_app = MagicMock(spec=ChatApplication)
        self.task = ChatApplicationTask("chat_app", {}, self.chat_app, print)

    def test_execute(self):
        context = WorkflowContext()
        context.set_global("processed_files", {"file1": "path/to/file1"})

        result = self.task.execute(context)

        self.chat_app.set_files.assert_called_once_with({"file1": "path/to/file1"})
        self.chat_app.run.assert_called_once()
        self.assertEqual(result["status"], "completed")

class TestMapTask(unittest.TestCase):
    def setUp(self):
        self.sub_task = MockTask("sub_task", {}, print)
        self.task = MapTask("map", {"iterable": "items"}, self.sub_task, print)

    def test_execute(self):
        context = WorkflowContext()
        context.set_global("items", [1, 2, 3])
        self.sub_task.execute = MagicMock(side_effect=[{"result": i * 2} for i in [1, 2, 3]])

        result = self.task.execute(context)

        self.assertEqual(self.sub_task.execute.call_count, 3)
        self.assertIn("_debug", result)
        self.assertEqual(len(result["_debug"]), 3)

class TestIfElseTask(unittest.TestCase):
    def setUp(self):
        self.if_task = MagicMock(spec=Task)
        self.else_task = MagicMock(spec=Task)
        self.task = IfElseTask("if_else", {"condition": "value > 5"}, self.if_task, print, self.else_task)

    def test_execute_if_true(self):
        context = WorkflowContext()
        context.set_global("value", 10)

        self.task.execute(context)

        self.if_task.execute.assert_called_once()
        self.else_task.execute.assert_not_called()

    def test_execute_if_false(self):
        context = WorkflowContext()
        context.set_global("value", 3)

        self.task.execute(context)

        self.if_task.execute.assert_not_called()
        self.else_task.execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()
