import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from hermes.interface.templates.template_manager import TemplateManager


@pytest.fixture
def template_dir(tmp_path):
    """Create a temporary directory with test templates"""
    test_dir = tmp_path / "test_templates"
    test_dir.mkdir()
    
    # Create a simple test template file
    simple_template = test_dir / "simple.mako"
    simple_template.write_text("Hello, ${name}!")
    
    # Create another template for testing get_template
    another_template = test_dir / "another.mako"
    another_template.write_text("Testing ${value}")
    
    return test_dir


class TestTemplateManager:
    def test_initialization(self, template_dir):
        """Test initialization with template directory"""
        manager = TemplateManager(template_dir)
        assert str(manager.template_dir) == str(template_dir)
        assert manager.lookup.directories[0] == str(template_dir)
    
    def test_render_template(self, template_dir):
        """Test rendering a template with context variables"""
        manager = TemplateManager(template_dir)
        result = manager.render_template("simple.mako", name="World")
        assert result == "Hello, World!"
    
    def test_get_template(self, template_dir):
        """Test getting a template object"""
        manager = TemplateManager(template_dir)
        template = manager.get_template("another.mako")
        assert template is not None
        # Verify we can render with the template directly
        rendered = template.render(value="success").decode('utf-8')
        assert rendered == "Testing success"
    
    def test_get_nonexistent_template(self, template_dir):
        """Test getting a template that doesn't exist"""
        manager = TemplateManager(template_dir)
        template = manager.get_template("nonexistent.mako")
        assert template is None
    
    def test_render_template_error(self, template_dir):
        """Test error handling in render_template"""
        manager = TemplateManager(template_dir)
        with pytest.raises(Exception):
            # Try to render a template that doesn't exist
            manager.render_template("nonexistent.mako")
