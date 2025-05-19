import traceback

from hermes.chat.interface.assistant.agent.deep_research.context.content_truncator import ContentTruncator
from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap, DynamicSectionData
from hermes.chat.interface.templates.template_manager import TemplateManager


class HistoryBlock:
    pass


class ChatMessage(HistoryBlock):
    """Represents a single message in the chat history"""

    def __init__(self, author: str, content: str):
        self.author = author
        self.content = content


class AutoReply(HistoryBlock):
    def __init__(
        self,
        error_report: str,
        command_outputs: list[tuple[str, dict]],
        messages: list[tuple[str, str]],
        confirmation_request: str | None = None,
        dynamic_sections: list[tuple[int, DynamicSectionData]] | None = None,
    ):
        self.error_report: str = error_report
        self.command_outputs: list[tuple[str, dict]] = command_outputs
        self.messages: list[tuple[str, str]] = messages
        self.confirmation_request: str | None = confirmation_request
        # Store the data objects, not rendered strings
        self.dynamic_sections: list[tuple[int, DynamicSectionData]] = dynamic_sections or []

    def generate_auto_reply(
        self,
        template_manager: TemplateManager,
        renderer_registry: DynamicDataTypeToRendererMap,
        future_changes_map: dict[int, int],
        per_command_output_maximum_length: int | None = None,
    ) -> str:
        """
        Generate an automatic reply using a Mako template, rendering dynamic sections on the fly.

        Args:
            template_manager: The template manager instance.
            renderer_registry: Maps data types to renderer instances.
            future_changes_map: Maps section index to its future change count.
            per_command_output_maximum_length: Optional max length for command outputs.

        Returns:
            Formatted automatic reply string.
        """
        # --- Render Dynamic Sections ---
        rendered_dynamic_sections: list[tuple[int, str]] = []
        for index, data_instance in self.dynamic_sections:
            data_type = type(data_instance)
            renderer = renderer_registry.get(data_type)
            future_changes = future_changes_map.get(index, 0)
            rendered_content = ""

            if not renderer:
                raise Exception(f"No renderer found for {data_type}")

            try:
                # Pass future_changes count to the renderer
                rendered_content = renderer.render(data_instance, future_changes)
            except Exception:
                # Error handling as requested: print stack trace and generate message
                print(f"\n--- ERROR RENDERING DYNAMIC SECTION (Index: {index}, Type: {data_type.__name__}) ---")
                tb_str = traceback.format_exc()
                print(tb_str)
                print("--- END ERROR ---")
                # Corrected f-string for artifact name
                artifact_name = f"render_error_section_{index}_{data_type.__name__}"
                rendered_content = (
                    f'<error context="Rendering dynamic section index {index} ({data_type.__name__})">\n'
                    f"**SYSTEM ERROR:** Failed to render this section. "
                    f"Please create an artifact named '{artifact_name}' "
                    f"with the following content:\n```\n{tb_str}\n```\n"
                    "Then, inform the administrator.\n"
                    "</error>"
                )

            rendered_dynamic_sections.append((index, rendered_content))

        # --- Prepare Context for Mako Template ---
        context = {
            "confirmation_request": self.confirmation_request,
            "error_report": self.error_report,
            "command_outputs": self.command_outputs,
            "messages": self.messages,
            "rendered_dynamic_sections": rendered_dynamic_sections,  # Pass rendered strings
            "per_command_output_maximum_length": per_command_output_maximum_length,
            "ContentTruncator": ContentTruncator,  # Still needed for command output truncation
        }

        # --- Render the Main Auto-Reply Template ---
        try:
            return template_manager.render_template("context/auto_reply.mako", **context)
        except Exception:
            # Handle potential errors in the main auto_reply.mako template itself
            print("\n--- ERROR RENDERING auto_reply.mako ---")
            tb_str = traceback.format_exc()
            print(tb_str)
            print("--- END ERROR ---")
            # Return a fallback error message if the main template fails
            return (
                f"# Automatic Reply\n\n"
                f"**SYSTEM ERROR:** Failed to render the main auto-reply structure.\n"
                f"Please report this error to the administrator.\n\n"
                f"Details:\n```\n{tb_str}\n```"
            )
