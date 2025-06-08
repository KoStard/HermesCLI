from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.commands import ResearchCommandContextFactory
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.assistant.deep_research.task_processor import TaskProcessor


class ResearchCommandContextFactoryImpl(ResearchCommandContextFactory[ResearchCommandContextImpl]):
    def create_command_context(
        self, task_processor: "TaskProcessor", current_node: "ResearchNode", command_processor: "CommandProcessor",
    ) -> ResearchCommandContextImpl:
        return ResearchCommandContextImpl(task_processor, command_processor, current_node)
