"""Fuzzy select command for the user control panel."""

from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.user.control_panel.fuzzy_selector import FuzzyFilesSelector
from hermes.chat.messages import TextualFileMessage


def _parse_fuzzy_select_command_wrapper(control_panel, content: str) -> MessageEvent:
    """Wrapper for fuzzy_select command that returns a single event"""
    events = _parse_fuzzy_select_command(control_panel, content)
    # Return the first event if there are any, otherwise a default message event
    if events:
        return events[0]
    # Return a default message if no files were selected
    return MessageEvent(
        TextualFileMessage(
            author="user",
            text_filepath=None,
            textual_content="No files were selected",
            file_role="notification",
        ),
    )


def _parse_fuzzy_select_command(control_panel, content: str) -> list[MessageEvent]:
    """Parse the /fuzzy_select command"""
    try:
        fuzzy_selector = FuzzyFilesSelector()
        absolute_file_paths = fuzzy_selector.select_files(multi=True)
        result_events: list[MessageEvent] = []
        for absolute_file_path in absolute_file_paths:
            result_events.append(
                MessageEvent(
                    TextualFileMessage(
                        author="user",
                        text_filepath=absolute_file_path,
                        textual_content=None,
                    ),
                ),
            )
        return result_events
    except Exception as e:
        control_panel.notifications_printer.print_notification(f"Error: {e}", control_panel.notifications_printer.CLIColors.RED)
    return []


def register() -> ControlPanelCommand:
    """Register the fuzzy select command."""
    return ControlPanelCommand(
        command_id="fuzzy_select",
        command_label="/fuzzy_select",
        description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
        short_description="Share a text-based document",
        parser=lambda line, control_panel: _parse_fuzzy_select_command_wrapper(control_panel, line),
        with_argument=False,
        is_chat_command=True,
        is_agent_command=True,
        is_research_command=True,
    )
