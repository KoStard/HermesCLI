from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.commands import CommandContextFactory
from hermes.chat.interface.assistant.deep_research.commands.command_context import CommandContextImpl


if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.assistant.deep_research.task_processor import TaskProcessor
    from hermes.chat.interface.assistant.deep_research.command_processor import CommandProcessor


class CommandContextFactoryImpl(CommandContextFactory[CommandContextImpl]):
    def create_command_context(
        self, task_processor: "TaskProcessor", current_node: "ResearchNode", command_processor: 'CommandProcessor'
    ) -> CommandContextImpl:
        return CommandContextImpl(task_processor, command_processor, current_node)
