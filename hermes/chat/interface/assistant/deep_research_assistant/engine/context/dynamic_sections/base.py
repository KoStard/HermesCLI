from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.templates.template_manager import (
        TemplateManager,
    )


@dataclass(frozen=True)
class DynamicSectionData:
    """Base class for dynamic section data. Frozen makes instances hashable."""

    pass


class DynamicSectionRenderer(ABC):
    """Base class for rendering dynamic sections."""

    def __init__(self, template_manager: "TemplateManager", template_name: str):
        self.template_manager = template_manager
        self.template_name = template_name

    @abstractmethod
    def render(self, data: "DynamicSectionData", future_changes: int) -> str:
        """
        Renders the section based on the provided data and future changes.

        Args:
            data: The specific data dataclass instance for this section.
            future_changes: The number of times this section changes *after*
                            the current instance in the history.

        Returns:
            The rendered HTML/Markdown string for the section, or an error message.
        """
        pass

    def _render_template(self, context: dict) -> str:
        """Helper to render the template with common error handling."""
        # Import traceback locally within the method to avoid potential circular dependencies
        # if this base class were to be imported widely, although less likely now.
        import traceback

        try:
            return self.template_manager.render_template(self.template_name, **context)
        except Exception:
            print(f"\n--- ERROR RENDERING TEMPLATE: {self.template_name} ---")
            tb_str = traceback.format_exc()
            print(tb_str)
            print("--- END ERROR ---")
            # Corrected f-string for artifact name
            artifact_name = f"render_error_{self.template_name.replace('/', '_').replace('.mako', '')}"
            error_message = (
                f"**SYSTEM ERROR:** Failed to render the '{self.template_name}' section. "
                f"Please create an artifact named '{artifact_name}' "
                f"with the following content:\n```\n{tb_str}\n```\n"
                "Then, inform the administrator."
            )
            # We might want to wrap this in XML tags appropriate for the interface
            # For now, return the raw error message for inclusion.
            return f'<error context="Rendering {self.template_name}">\n{error_message}\n</error>'
