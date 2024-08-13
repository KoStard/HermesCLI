import unittest
import tempfile
import os
from hermes.utils.file_utils import is_binary, process_file_name

class TestFileUtils(unittest.TestCase):
    def test_is_binary(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b'Hello, World!')
        self.assertFalse(is_binary(tf.name))
        os.unlink(tf.name)

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b'\x00\x01\x02\x03')
        self.assertTrue(is_binary(tf.name))
        os.unlink(tf.name)

    def test_process_file_name(self):
        self.assertEqual(process_file_name('test_file.txt'), 'test_file')
        self.assertEqual(process_file_name('path/to/file.py'), 'file')
        self.assertEqual(process_file_name('file with spaces.md'), 'file_with_spaces')
        self.assertEqual(process_file_name('FILE_WITH_CAPS.TXT'), 'file_with_caps')

if __name__ == '__main__':
    unittest.main()
