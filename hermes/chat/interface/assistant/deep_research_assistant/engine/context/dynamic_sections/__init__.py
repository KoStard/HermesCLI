from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, ClassVar, Optional

if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import TemplateManager


@dataclass(frozen=True)
class DynamicSectionData:
    """Base class for dynamic section data. Frozen makes instances hashable."""

    # Class registry for type lookup during deserialization
    _registry: ClassVar[dict[str, type['DynamicSectionData']]] = {}

    def serialize(self) -> dict[str, Any]:
        """
        Serialize this instance to a dictionary for JSON storage.
        Default implementation uses dataclasses.asdict.
        """
        return {
            "type": self.__class__.__name__,
            "data": asdict(self)
        }

    @classmethod
    def register_type(cls, data_class: type['DynamicSectionData']) -> None:
        """Register a DynamicSectionData subclass in the registry."""
        cls._registry[data_class.__name__] = data_class

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Optional['DynamicSectionData']:
        """
        Deserialize from a dictionary (previously serialized with serialize()).
        """
        if not data or "type" not in data or "data" not in data:
            return None

        type_name = data["type"]
        if type_name not in cls._registry:
            print(f"Warning: Unknown dynamic section type '{type_name}' during deserialization")
            return None

        data_class = cls._registry[type_name]

        # Filter the data dictionary to only include fields present in the dataclass
        field_names = {f.name for f in fields(data_class)}
        filtered_data = {k: v for k, v in data["data"].items() if k in field_names}

        try:
            # Create an instance of the dataclass with the deserialized data
            return data_class(**filtered_data)
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
