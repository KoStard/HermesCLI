import unittest

from hermes.chat.interface.markdown.section_finder import SectionFinder


class TestSectionFinder(unittest.TestCase):
    def setUp(self):
        self.finder = SectionFinder()

    def test_find_section_end(self):
        """Test finding the end of a section."""
        lines = [
            "Content 1\n",
            "# New Section\n",
            "Content 2\n",
        ]

        end_idx = self.finder.find_section_end(lines, 1)
        self.assertEqual(end_idx, 1)

        # Test with no ending section
        lines = ["Content 1\n", "Content 2\n"]
        end_idx = self.finder.find_section_end(lines, 1)
        self.assertEqual(end_idx, 2)

    def test_find_start_of_next_section(self):
        """Test finding the start of the next section."""
        lines = [
            "Content 1\n",
            "Content 2\n",
            "# New Section\n",
        ]

        start_idx = self.finder.find_start_of_next_section(lines)
        self.assertEqual(start_idx, 2)

        # Test with no next section
        lines = ["Content 1\n", "Content 2\n"]
        start_idx = self.finder.find_start_of_next_section(lines)
        self.assertEqual(start_idx, 2)

    def test_find_section(self):
        """Test finding a specific section."""
        lines = [
            "# Section 1\n",
            "Content 1\n",
            "## Subsection 1.1\n",
            "Content 1.1\n",
            "# Section 2\n",
            "Content 2\n",
        ]

        # Find top-level section
        start, end, found = self.finder.find_section(lines, ["Section 1"])
        self.assertTrue(found)
        self.assertEqual(start, 0)

        # Find nested section
        start, end, found = self.finder.find_section(lines, ["Section 1", "Subsection 1.1"])
        self.assertTrue(found)
        self.assertEqual(start, 2)

        # Section not found
        start, end, found = self.finder.find_section(lines, ["Section 3"])
        self.assertFalse(found)


if __name__ == "__main__":
    unittest.main()
