from collections.abc import Generator
from typing import Any

from hermes.chat.events import AssistantDoneEvent, Event, MessageEvent
from hermes.chat.interface.assistant.chat.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.messages import TextMessage


class DoneCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Mark a task as done and provide a final report."""

    def __init__(self):
        super().__init__(
            "done",
            """Mark the current task as done and provide a final report to the user.

You can take as many steps as you need to accomplish the task before running this command.
The report should summarize what you've done, any issues encountered, and the final results.

IMPORTANT: Only use this command when you have actually completed the task.
If you run this command without finishing the task, it will cause loss of user trust.
Make sure you have finished and read through all the command outputs before marking the task as done.""",
        )
        self.add_section("report", True, "Final report summarizing what was accomplished")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        report_content = args["report"]

        context.print_notification("Agent marked task as done")
        yield AssistantDoneEvent()
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=report_content,
                text_role="AgentReport",
                name="Task Completion Report",
            )
        )

    def get_additional_information(self):
        return {"is_agent_only": True}
