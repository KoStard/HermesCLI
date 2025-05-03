from pathlib import Path
from typing import Any, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mako.template import Template
    from mako.lookup import TemplateLookup


class TemplateManager:
    """Manages loading and rendering of Mako templates for Hermes interfaces"""

    def __init__(self, template_dir):
        """
        Initialize the template manager with a specific template directory.

        Args:
            template_dir: Path to directory containing template files
        """
        self.template_dir = Path(template_dir)
        self._lookup = None

    @property
    def lookup(self) -> "TemplateLookup":
        from mako.lookup import TemplateLookup

        if self._lookup is None:
            self._lookup = TemplateLookup(
                directories=[str(self.template_dir)],
                module_directory="/tmp/mako_modules",  # For template caching
                input_encoding="utf-8",
                output_encoding="utf-8",
                encoding_errors="replace",
            )
        return self._lookup

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
            return template.render(**context).decode("utf-8")
        except Exception as e:
            # For now return a basic error message, we'll improve error handling later
            print(f"Error rendering template {template_name}: {str(e)}")
            raise

    def get_template(self, template_name: str) -> Optional["Template"]:
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
