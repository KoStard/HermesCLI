import unittest
from unittest.mock import patch, MagicMock
from hermes.context_providers.update_context_provider import UpdateContextProvider
from hermes.config import HermesConfig

class TestUpdateContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = UpdateContextProvider()

    def test_is_used(self):
        self.provider.file_path = ""
        self.assertFalse(self.provider.is_used())
        
        self.provider.file_path = "test.txt"
        self.assertTrue(self.provider.is_used())

if __name__ == '__main__':
    unittest.main()
