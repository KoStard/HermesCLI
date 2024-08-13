import unittest
import tempfile
import os
from hermes.file_processors.default import DefaultFileProcessor
from hermes.file_processors.bedrock import BedrockFileProcessor

class TestDefaultFileProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DefaultFileProcessor()

    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
            tf.write('Hello, World!')
        content = self.processor.read_file(tf.name)
        self.assertEqual(content, 'Hello, World!')
        os.unlink(tf.name)

    def test_write_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            pass
        self.processor.write_file(tf.name, 'Test content')
        with open(tf.name, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Test content')
        os.unlink(tf.name)

class TestBedrockFileProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BedrockFileProcessor()

    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tf:
            tf.write(b'Hello, World!')
        content = self.processor.read_file(tf.name)
        self.assertEqual(content, b'Hello, World!')
        os.unlink(tf.name)

    def test_write_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            pass
        self.processor.write_file(tf.name, 'Test content')
        with open(tf.name, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Test content')
        os.unlink(tf.name)

if __name__ == '__main__':
    unittest.main()
