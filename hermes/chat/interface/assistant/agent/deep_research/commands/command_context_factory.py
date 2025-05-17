from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.deep_research.commands.command_context import CommandContextImpl
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.engine import AgentEngine
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


class CommandContextFactoryImpl(CommandContextFactory[CommandContextImpl]):
    def create_command_context(self, engine: "AgentEngine", current_state_machine_node: "TaskTreeNode") -> CommandContextImpl:
        return CommandContextImpl(engine, current_state_machine_node)
