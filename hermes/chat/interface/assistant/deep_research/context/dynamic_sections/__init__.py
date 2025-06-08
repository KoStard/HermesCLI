from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import jsonpickle

if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import TemplateManager


@dataclass(frozen=True)
class DynamicSectionData:
    """Base class for dynamic section data. Frozen makes instances hashable."""

    def serialize(self) -> dict[str, Any]:
        """Serialize this instance to a dictionary for JSON storage.
        Uses jsonpickle for robust serialization of nested structures.
        """
        return {"type": self.__class__.__name__, "data": jsonpickle.encode(self)}

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Optional["DynamicSectionData"]:
        """Deserialize from a dictionary (previously serialized with serialize()).
        Uses jsonpickle for robust deserialization of nested structures.
        """
        if not data or "type" not in data or "data" not in data:
            return None

        type_name = data["type"]

        try:
            # Use jsonpickle to decode the serialized object
            return jsonpickle.decode(data["data"])
        except Exception as e:
            print(f"Error deserializing {type_name}: {e}")
            return None


class DynamicSectionRenderer(ABC):
    """Base class for rendering dynamic sections."""

    def __init__(self, template_manager: "TemplateManager", template_name: str):
        self.template_manager = template_manager
        self.template_name = template_name

    @abstractmethod
    def render(self, data: "DynamicSectionData", future_changes: int) -> str:
        """Renders the section based on the provided data and future changes.

        Args:
            data: The specific data dataclass instance for this section.
            future_changes: The number of times this section changes *after*
                            the current instance in the history.

        Returns:
            The rendered HTML/Markdown string for the section, or an error message.
        """

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


DynamicDataTypeToRendererMap = dict[type["DynamicSectionData"], "DynamicSectionRenderer"]
