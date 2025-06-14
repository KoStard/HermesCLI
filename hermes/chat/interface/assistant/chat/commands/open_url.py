from collections.abc import Generator
from typing import Any

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.assistant.chat.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.interface.helpers.cli_notifications import CLIColors
from hermes.chat.messages import UrlMessage


class OpenUrlCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Read and return the contents of a URL."""

    def __init__(self):
        super().__init__(
            "open_url",
            """Read and return the contents of a URL.

This command fetches content from the specified URL and returns it for your analysis.
Use this after a web search to read specific pages, or when the user provides you with a URL.

If Exa API is configured, it will be used to get enhanced content.""",
        )
        self.add_section("url", True, "URL to fetch content from (must be a valid, complete URL)")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        url = args["url"].strip()

        if not url:
            error_msg = "Error: No URL provided"
            context.print_notification(error_msg, CLIColors.RED)
            yield context.create_assistant_notification(error_msg, "URL Error")
            return

        context.print_notification(f"Opening URL: {url}")
        yield MessageEvent(UrlMessage(author="user", url=url))

    def get_additional_information(self):
        return {"is_agent_only": True}
