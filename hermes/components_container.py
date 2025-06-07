from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.chat.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.assistant.models.model_factory import ModelFactory
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.participants import DebugParticipant, LLMParticipant, UserParticipant

if TYPE_CHECKING:
    from hermes.mcp.mcp_manager import McpManager


@dataclass
class CoreComponents:
    model_factory: ModelFactory
    user_control_panel: UserControlPanel
    llm_control_panel: ChatAssistantControlPanel
    extension_utils_builders: list
    extension_deep_research_commands: list
    mcp_manager: "McpManager"


@dataclass
class Participants:
    user: UserParticipant
    assistant: LLMParticipant | DebugParticipant
