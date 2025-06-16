import textwrap
from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ResearchNode
from hermes.chat.interface.commands.command import Command


class SendMessageToCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "send_message_to",
            textwrap.dedent("""
            Send a message to your teammate assigned to one of your subproblems.
            This command will not change the status of the command.
            If your goal is to send additional instructions, you can use activate_subproblems command afterwards.
            """),
        )
        self.add_section("message", True, "Content of the message")
        self.add_section("subproblem_title", True, "Title of the subproblem")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        message = args["message"]
        subproblem_title = args["subproblem_title"]
        child_node = self._find_child_node(context, subproblem_title)
        if not child_node:
            context.add_command_output(self.name, args, f"Error: Subproblem {subproblem_title} wasn't found, message not sent.")
            return
        child_node.get_history().get_auto_reply_aggregator().add_internal_message_from(message, context.current_node.get_title())
        context.add_command_output(self.name, args, "Message successfully sent.")

    def _find_child_node(self, context: ResearchCommandContextImpl, subproblem_title: str) -> ResearchNode | None:
        child_nodes = context.current_node.list_child_nodes()
        for child_node in child_nodes:
            if child_node.get_title() == subproblem_title:
                return child_node
        return None
