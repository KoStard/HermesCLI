from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.deep_research.commands.command_context import CommandContextImpl
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor


class CommandContextFactoryImpl(CommandContextFactory[CommandContextImpl]):
    def create_command_context(
        self, task_processor: "TaskProcessor", current_node: "ResearchNode", command_processor: "CommandProcessor"
    ) -> CommandContextImpl:
        return CommandContextImpl(task_processor, command_processor, current_node)
