import unittest

from hermes.chat.interface.markdown.content_processor import ContentProcessor


class TestContentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = ContentProcessor()

    def test_update_section_simple(self):
        """Test updating a simple section."""
        lines = [
            "# Section 1\n",
            "Content 1\n",
            "# Section 2\n",
            "Content 2\n",
        ]
        section_path = ["Section 2"]
        new_content = "New content\n"

        updated_lines, found = self.processor.process_content(
            lines, section_path, new_content, "update_markdown_section"
        )

        self.assertTrue(found)
        self.assertEqual(updated_lines, [
            "# Section 1\n",
            "Content 1\n",
            "# Section 2\n",
            "New content\n",
        ])

    def test_append_section_simple(self):
        """Test appending to a simple section."""
        lines = [
            "# Section 1\n",
            "Content 1\n",
            "# Section 2\n",
            "Content 2\n",
        ]
        section_path = ["Section 2"]
        new_content = "Appended content\n"

        updated_lines, found = self.processor.process_content(
            lines, section_path, new_content, "append_markdown_section"
        )

        self.assertTrue(found)
        self.assertEqual(updated_lines, [
            "# Section 1\n",
            "Content 1\n",
            "# Section 2\n",
            "Content 2\n",
            "Appended content\n",
        ])

    def test_nested_section_update(self):
        """Test updating a nested section."""
        lines = [
            "# Section 1\n",
            "Content 1\n",
            "## Subsection 1.1\n",
            "Content 1.1\n",
            "# Section 2\n",
            "Content 2\n",
        ]
        section_path = ["Section 1", "Subsection 1.1"]
        new_content = "New subsection content\n"

        updated_lines, found = self.processor.process_content(
            lines, section_path, new_content, "update_markdown_section"
        )

        self.assertTrue(found)
        self.assertEqual(updated_lines, [
            "# Section 1\n",
            "Content 1\n",
            "## Subsection 1.1\n",
            "New subsection content\n",
            "# Section 2\n",
            "Content 2\n",
        ])

    def test_preface_update(self):
        """Test updating a section's preface."""
        lines = [
            "# Section 1\n",
            "Preface content\n",
            "## Subsection 1.1\n",
            "Content 1.1\n",
        ]
        section_path = ["Section 1", "__preface"]
        new_content = "New preface\n"

        updated_lines, found = self.processor.process_content(
            lines, section_path, new_content, "update_markdown_section", True
        )

        self.assertTrue(found)
        self.assertEqual(updated_lines, [
            "# Section 1\n",
            "New preface\n",
            "## Subsection 1.1\n",
            "Content 1.1\n",
        ])

    def test_section_not_found(self):
        """Test when section is not found."""
        lines = [
            "# Section 1\n",
            "Content 1\n",
        ]
        section_path = ["Section 2"]
        new_content = "New content\n"

        updated_lines, found = self.processor.process_content(
            lines, section_path, new_content, "update_markdown_section"
        )

        self.assertFalse(found)
        self.assertEqual(updated_lines, lines)

    def test_invalid_mode(self):
        """Test with invalid mode."""
        lines = ["# Section 1\n"]
        section_path = ["Section 1"]
        new_content = "New content\n"

        with self.assertRaises(ValueError):
            self.processor.process_content(lines, section_path, new_content, "invalid_mode")


if __name__ == "__main__":
    unittest.main()
