from dataclasses import dataclass

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact


@dataclass(frozen=True)
class NodeState:
    artifacts_status: dict[Artifact, bool]
