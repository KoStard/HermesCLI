from pathlib import Path
from typing import Any, Dict, Optional
from mako.lookup import TemplateLookup
from mako.template import Template

class TemplateManager:
    """Manages loading and rendering of Mako templates for the Deep Research interface"""

    def __init__(self, template_dir=None):
        if not template_dir:
            self.template_dir = Path(__file__).parent
        else:
            self.template_dir = template_dir
        self.lookup = TemplateLookup(
            directories=[str(self.template_dir)],
            module_directory='/tmp/mako_modules',  # For template caching
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace'
        )

    def render_template(self, template_name: str, **context: Any) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file (e.g. 'base.mako')
            **context: Template context variables
            
        Returns:
            Rendered template as string
        """
        try:
            template = self.lookup.get_template(template_name)
            return template.render(**context).decode('utf-8')
        except Exception as e:
            # For now return a basic error message, we'll improve error handling later
            print(f"Error rendering template {template_name}: {str(e)}")
            raise

    def get_template(self, template_name: str) -> Optional[Template]:
        """
        Get a template object for the given template name.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template object or None if not found
        """
        try:
            return self.lookup.get_template(template_name)
        except Exception:
            return None
