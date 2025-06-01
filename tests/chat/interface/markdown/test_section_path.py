import unittest

from hermes.chat.interface.markdown.header import Header
from hermes.chat.interface.markdown.section_path import SectionPath


class TestSectionPath(unittest.TestCase):
    def test_standard_hierarchy(self):
        """Test standard H1, H2, H3 hierarchy."""
        path = SectionPath()
        
        # Add H1 header
        path.update(Header("# Section 1\n", 1, "Section 1"))
        self.assertEqual(path.current_path, ["Section 1"])
        self.assertEqual(path.get_min_level(), 1)
        
        # Add H2 header
        path.update(Header("## Subsection 1.1\n", 2, "Subsection 1.1"))
        self.assertEqual(path.current_path, ["Section 1", "Subsection 1.1"])
        
        # Add H3 header
        path.update(Header("### Detail 1.1.1\n", 3, "Detail 1.1.1"))
        self.assertEqual(path.current_path, ["Section 1", "Subsection 1.1", "Detail 1.1.1"])
        
        # Add another H2 header (should replace H2 and H3)
        path.update(Header("## Subsection 1.2\n", 2, "Subsection 1.2"))
        self.assertEqual(path.current_path, ["Section 1", "Subsection 1.2"])

    def test_non_h1_start(self):
        """Test hierarchy starting with H2."""
        path = SectionPath()
        
        # Start with H2 header
        path.update(Header("## Section 1\n", 2, "Section 1"))
        self.assertEqual(path.current_path, ["Section 1"])
        self.assertEqual(path.get_min_level(), 2)
        
        # Add H3 header
        path.update(Header("### Subsection 1.1\n", 3, "Subsection 1.1"))
        self.assertEqual(path.current_path, ["Section 1", "Subsection 1.1"])
        
        # Add another H2 header
        path.update(Header("## Section 2\n", 2, "Section 2"))
        self.assertEqual(path.current_path, ["Section 2"])

    def test_h3_start(self):
        """Test hierarchy starting with H3."""
        path = SectionPath()
        
        # Start with H3 header
        path.update(Header("### Deep Section\n", 3, "Deep Section"))
        self.assertEqual(path.current_path, ["Deep Section"])
        self.assertEqual(path.get_min_level(), 3)
        
        # Add H4 header
        path.update(Header("#### Deeper\n", 4, "Deeper"))
        self.assertEqual(path.current_path, ["Deep Section", "Deeper"])
        
        # Add H5 header
        path.update(Header("##### Deepest\n", 5, "Deepest"))
        self.assertEqual(path.current_path, ["Deep Section", "Deeper", "Deepest"])
        
        # Add H3 header (should reset path)
        path.update(Header("### Another Section\n", 3, "Another Section"))
        self.assertEqual(path.current_path, ["Another Section"])

    def test_mixed_levels(self):
        """Test with mixed header levels."""
        path = SectionPath()
        
        # Start with H3
        path.update(Header("### Start H3\n", 3, "Start H3"))
        self.assertEqual(path.current_path, ["Start H3"])
        self.assertEqual(path.get_min_level(), 3)
        
        # Add H2 (lower level than starting point)
        path.update(Header("## Higher H2\n", 2, "Higher H2"))
        self.assertEqual(path.current_path, ["Higher H2"])
        self.assertEqual(path.get_min_level(), 2)  # Min level should update
        
        # Add H4
        path.update(Header("#### H4 Detail\n", 4, "H4 Detail"))
        self.assertEqual(path.current_path, ["Higher H2", "H4 Detail"])
        
        # Add H1 (even lower level)
        path.update(Header("# Top Level\n", 1, "Top Level"))
        self.assertEqual(path.current_path, ["Top Level"])
        self.assertEqual(path.get_min_level(), 1)  # Min level should update again


if __name__ == "__main__":
    unittest.main()
