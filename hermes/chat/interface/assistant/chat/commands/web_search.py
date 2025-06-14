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
from hermes.chat.messages import TextualFileMessage


class WebSearchCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Perform a web search using Exa API."""

    def __init__(self):
        super().__init__(
            "web_search",
            """Perform a web search using the Exa API.

This command returns up to 10 relevant results from the web based on your query.
Each result includes the title, URL, and when available, author and publication date.

IMPORTANT: This API costs the user money. Only use this command when directly asked to do a web search,
or when you absolutely need up-to-date information that isn't in your knowledge cutoff.""",
        )
        self.add_section("query", True, "Search query - be specific for better results")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        query = args["query"]

        # Validate Exa client
        if not context.exa_client:
            yield from self._handle_missing_client(context)
            return

        try:
            yield from self._perform_search(context, query)
        except Exception as e:
            yield from self._handle_search_error(context, e, query)

    def _handle_missing_client(self, context: ChatAssistantCommandContext) -> Generator[Event, None, None]:
        """Handle case when Exa client is not configured"""
        error_msg = "Error: Exa client not configured"
        context.print_notification(error_msg, CLIColors.RED)
        yield context.create_assistant_notification(error_msg, "Web Search Error")

    def _perform_search(self, context: ChatAssistantCommandContext, query: str) -> Generator[Event, None, None]:
        """Execute the search and return results"""
        context.print_notification(f"Performing web search for: {query}")
        results = context.exa_client.search(query, num_results=10)

        if not results:
            yield context.create_assistant_notification(f"No results found for: {query}", "Web Search Results")
            return

        result_text = self._format_search_results(query, results)
        yield MessageEvent(self._create_results_message(query, result_text))
        yield context.create_assistant_notification(f"Completed web search for: {query}", "Web Search Complete")

    def _format_search_results(self, query: str, results) -> list[str]:
        """Format search results as text lines"""
        result_text = [f"# Web Search Results for: {query}\n"]
        for i, result in enumerate(results, 1):
            self._append_result_details(result_text, i, result)
        return result_text

    def _append_result_details(self, result_text: list[str], index: int, result) -> None:
        """Add details of a single search result to the result text"""
        result_text.append(f"Result {index}:")
        result_text.append(f"  Title: {result.title}")
        result_text.append(f"  URL: {result.url}")
        if result.author:
            result_text.append(f"  Author: {result.author}")
        if result.published_date:
            result_text.append(f"  Published: {result.published_date}")
        result_text.append("")

    def _create_results_message(self, query: str, result_text: list[str]) -> TextualFileMessage:
        """Create message with search results"""
        return TextualFileMessage(
            author="user",
            text_filepath=None,
            textual_content="\n".join(result_text),
            file_role="WebSearchResults",
            name=f"Web Search: {query}",
        )

    def _handle_search_error(self, context: ChatAssistantCommandContext, error: Exception, query: str) -> Generator[Event, None, None]:
        """Handle search execution errors"""
        error_msg = f"Error performing web search: {str(error)}"
        context.print_notification(error_msg, CLIColors.RED)
        yield context.create_assistant_notification(error_msg, "Web Search Error")

    def get_additional_information(self):
        return {"is_agent_only": True}
