"""Engine commands are commands that the engine can execute."""

from hermes.chat.events.engine_commands.agent_mode import AgentModeEvent
from hermes.chat.events.engine_commands.assistant_done import AssistantDoneEvent
from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.events.engine_commands.clear_history import ClearHistoryEvent
from hermes.chat.events.engine_commands.create_research import CreateResearchEvent
from hermes.chat.events.engine_commands.deep_research_budget import DeepResearchBudgetEvent
from hermes.chat.events.engine_commands.exit import ExitEvent
from hermes.chat.events.engine_commands.file_edit import FileEditEvent
from hermes.chat.events.engine_commands.list_research import ListResearchEvent
from hermes.chat.events.engine_commands.llm_commands_execution import LLMCommandsExecutionEvent
from hermes.chat.events.engine_commands.load_history import LoadHistoryEvent
from hermes.chat.events.engine_commands.once import OnceEvent
from hermes.chat.events.engine_commands.save_history import SaveHistoryEvent
from hermes.chat.events.engine_commands.switch_research import SwitchResearchEvent
from hermes.chat.events.engine_commands.thinking_level import ThinkingLevelEvent

__all__ = [
    "EngineCommandEvent",
    "ClearHistoryEvent",
    "SaveHistoryEvent",
    "LoadHistoryEvent",
    "ExitEvent",
    "AgentModeEvent",
    "FileEditEvent",
    "AssistantDoneEvent",
    "LLMCommandsExecutionEvent",
    "OnceEvent",
    "ThinkingLevelEvent",
    "DeepResearchBudgetEvent",
    "CreateResearchEvent",
    "SwitchResearchEvent",
    "ListResearchEvent",
]
