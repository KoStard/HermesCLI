import unittest
from unittest.mock import patch, MagicMock
from hermes.context_providers.fill_gaps_context_provider import FillGapsContextProvider
from hermes.config import HermesConfig

class TestFillGapsContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = FillGapsContextProvider()

    def test_is_used(self):
        self.provider.file_path = ""
        self.assertFalse(self.provider.is_used())
        
        self.provider.file_path = "test.txt"
        self.assertTrue(self.provider.is_used())

if __name__ == '__main__':
    unittest.main()
