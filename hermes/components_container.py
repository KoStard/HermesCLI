from dataclasses import dataclass

from hermes.chat.interface.assistant.chat_assistant.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.assistant.models.model_factory import ModelFactory
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.participants import Participant


@dataclass
class CoreComponents:
    model_factory: ModelFactory
    user_control_panel: UserControlPanel
    llm_control_panel: ChatAssistantControlPanel
    extension_utils_builders: list
    deep_research_commands: list


@dataclass
class Participants:
    user: Participant
    assistant: Participant