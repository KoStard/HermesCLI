from collections.abc import Generator
from typing import Any

from hermes.chat.events import AssistantDoneEvent, Event, MessageEvent
from hermes.chat.interface.assistant.chat_assistant.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.messages import TextMessage


class AskTheUserCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Ask the user for clarification or information."""

    def __init__(self):
        super().__init__(
            "ask_the_user",
            """Ask the user for clarification or specific information needed to complete the task.

Use this when you need additional information from the user to proceed.
Be specific and clear about what information you need.
Try to compile multiple related questions into a single request to minimize user interventions.

Running this command will end your current turn and wait for the user's response.""",
        )
        self.add_section(
            "question",
            True,
            "Question(s) for the user - be specific about what you need",
        )

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        question_content = args["question"]

        context.print_notification("Agent is asking the user a question")
        yield AssistantDoneEvent()
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=question_content,
                text_role="AgentQuestion",
                name="Task Related Question",
            )
        )

    def get_additional_information(self):
        return {"is_agent_only": True}
