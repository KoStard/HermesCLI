import unittest
from unittest.mock import patch, MagicMock
from hermes.context_providers.append_context_provider import AppendContextProvider
from hermes.config import HermesConfig

class TestAppendContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = AppendContextProvider()

    def test_is_used(self):
        self.provider.file_path = ""
        self.assertFalse(self.provider.is_used())
        
        self.provider.file_path = "test.txt"
        self.assertTrue(self.provider.is_used())

if __name__ == '__main__':
    unittest.main()
