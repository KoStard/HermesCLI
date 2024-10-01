import unittest
from unittest.mock import mock_open, patch, Mock
from hermes.file_processors.default import DefaultFileProcessor

class TestDefaultFileProcessor(unittest.TestCase):
    def setUp(self):
        self.file_processor = DefaultFileProcessor()

    @patch('os.path.exists')
    def test_read_file_nonexistent(self, mock_exists):
        mock_exists.return_value = False
        result = self.file_processor.read_file("nonexistent.txt")
        self.assertEqual(result, "empty")

    @patch('builtins.open', new_callable=mock_open, read_data="Hello, world!")
    @patch('os.path.exists')
    def test_read_file_text(self, mock_exists, mock_file):
        mock_exists.return_value = True
        result = self.file_processor.read_file("test.txt")
        self.assertEqual(result, "Hello, world!")

    @patch('PyPDF2.PdfReader')
    @patch('os.path.exists')
    def test_read_file_pdf(self, mock_exists, mock_pdf_reader):
        mock_exists.return_value = True
        mock_pdf_reader.return_value.pages = [Mock(extract_text=Mock(return_value="PDF content"))]
        
        with patch('builtins.open', mock_open()):
            result = self.file_processor.read_file("test.pdf")
        
        self.assertEqual(result, "PDF content")

    @patch('docx.Document')
    @patch('os.path.exists')
    def test_read_file_docx(self, mock_exists, mock_document):
        mock_exists.return_value = True
        mock_document.return_value.paragraphs = [Mock(text="DOCX content")]
        
        with patch('builtins.open', mock_open()):
            result = self.file_processor.read_file("test.docx")
        
        self.assertEqual(result, "DOCX content")

if __name__ == '__main__':
    unittest.main()
