from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.deep_research.commands.command_context import CommandContextImpl
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


class CommandContextFactoryImpl(CommandContextFactory[CommandContextImpl]):
    def create_command_context(
        self, task_processor: "TaskProcessor", current_task_tree_node: "TaskTreeNode", command_processor: "CommandProcessor"
    ) -> CommandContextImpl:
        return CommandContextImpl(task_processor, current_task_tree_node, command_processor)
