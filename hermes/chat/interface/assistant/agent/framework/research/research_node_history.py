from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class ResearchNodeHistory:
    def __init__(self, research_node: "ResearchNode"):
        pass

    def get_history_messages(self) -> list[dict]:
        pass
