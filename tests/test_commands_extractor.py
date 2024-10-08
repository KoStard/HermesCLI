import unittest
from hermes.utils.commands_extractor import extract_commands

class TestCommandsExtractor(unittest.TestCase):
    def setUp(self):
        self.commands_set = {'command1', 'command2', 'command3'}

    def test_single_command(self):
        source = "/command1 arg1 arg2"
        expected = [('/command1', 'arg1 arg2')]
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_multiple_commands(self):
        source = "/command1 arg1 arg2\n/command2 arg3\n/command3 arg4 arg5"
        expected = [
            ('/command1', 'arg1 arg2'),
            ('/command2', 'arg3'),
            ('/command3', 'arg4 arg5')
        ]
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_default_command(self):
        source = "some text\n/command1 arg1\nmore text"
        expected = [
            ('/prompt', 'some text'),
            ('/command1', 'arg1'),
            ('/prompt', 'more text')
        ]
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_mixed_content(self):
        source = "initial text\n/command1 arg1 arg2\nsome other text\n/command2 arg3 /command3 arg4\nfinal text"
        expected = [
            ('/prompt', 'initial text'),
            ('/command1', 'arg1 arg2'),
            ('/prompt', 'some other text'),
            ('/command2', 'arg3'),
            ('/command3', 'arg4'),
            ('/prompt', 'final text')
        ]
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_empty_input(self):
        source = ""
        expected = []
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_unknown_command(self):
        source = "/unknown_command arg1 arg2"
        expected = [('/prompt', '/unknown_command arg1 arg2')]
        self.assertEqual(extract_commands(source, self.commands_set), expected)

    def test_custom_default_command(self):
        source = "some text\n/command1 arg1\nmore text"
        expected = [
            ('/custom', 'some text'),
            ('/command1', 'arg1'),
            ('/custom', 'more text')
        ]
        self.assertEqual(extract_commands(source, self.commands_set, default_command='/custom'), expected)