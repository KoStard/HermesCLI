from collections import defaultdict
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
    InitialInterface,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode
    from hermes.chat.interface.templates.template_manager import TemplateManager


class ResearchNodeHistoryAdapter:
    """Extended version of ResearchNodeHistory that adds LLM-specific history management"""

    def __init__(self, research_node: "ResearchNode"):
        self.research_node = research_node

    def get_history_messages(
        self,
        template_manager: "TemplateManager",
        renderer_registry: "DynamicDataTypeToRendererMap",
        help_interface: str | None,
    ) -> list[dict[str, str]]:
        """Compiles and renders historical messages for LLM input."""
        compiled_blocks = self.research_node.get_history().get_compiled_blocks()

        # Process blocks in reverse order (newest to oldest)
        history_messages = self._process_history_blocks(compiled_blocks, template_manager, renderer_registry)

        # Return in chronological order
        return history_messages[::-1]

    def _process_history_blocks(
        self, compiled_blocks: list, template_manager: "TemplateManager", renderer_registry: "DynamicDataTypeToRendererMap"
    ) -> list[dict[str, str]]:
        """Process history blocks and convert them to message format."""
        history_messages = []
        auto_reply_counter = 0
        iterative_auto_reply_max_length = 5000

        for i in range(len(compiled_blocks) - 1, -1, -1):
            block = compiled_blocks[i]
            if isinstance(block, ChatMessage):
                history_messages.append(self._process_chat_message(block))
            elif isinstance(block, InitialInterface):
                history_messages.append(self._process_initial_interface(block, compiled_blocks, i, template_manager, renderer_registry))
            elif isinstance(block, AutoReply):
                auto_reply_counter, max_length = self._update_auto_reply_counters(auto_reply_counter, iterative_auto_reply_max_length)
                history_messages.append(
                    self._process_auto_reply(block, compiled_blocks, i, auto_reply_counter, max_length, template_manager, renderer_registry)
                )

        return history_messages

    def _process_chat_message(self, block: ChatMessage) -> dict[str, str]:
        """Convert a ChatMessage block to message dict format."""
        return {"author": block.author, "content": block.content}

    def _update_auto_reply_counters(self, counter: int, max_length: int) -> tuple[int, int | None]:
        """Update auto reply counters and determine max length."""
        counter += 1
        current_max_len = None

        if counter > 3:
            current_max_len = max_length
            max_length = max(max_length // 2, 300)

        return counter, current_max_len

    def _process_initial_interface(
        self,
        block,  # InitialInterface
        blocks: list,
        index: int,
        template_manager: "TemplateManager",
        renderer_registry: "DynamicDataTypeToRendererMap",
    ) -> dict[str, str]:
        """Process an InitialInterface block into message dict format."""
        future_changes_map = self._calculate_future_changes(blocks, index)
        content = block.generate_interface_content(template_manager, renderer_registry, future_changes_map)
        return {"author": "user", "content": content}

    def _process_auto_reply(
        self,
        block: AutoReply,
        blocks: list,
        index: int,
        counter: int,
        max_length: int | None,
        template_manager: "TemplateManager",
        renderer_registry: "DynamicDataTypeToRendererMap",
    ) -> dict[str, str]:
        """Process an AutoReply block into message dict format."""
        content = self._render_auto_reply_block_for_llm(block, blocks, index, counter, max_length, template_manager, renderer_registry)
        return {"author": "user", "content": content}

    def _render_auto_reply_block_for_llm(
        self,
        block: AutoReply,
        compiled_blocks: list,
        current_block_index: int,
        auto_reply_counter: int,
        auto_reply_max_length: int | None,
        template_manager: "TemplateManager",
        renderer_registry: "DynamicDataTypeToRendererMap",
    ) -> str:
        """Renders a single AutoReply block for LLM history."""
        future_changes_map = self._calculate_future_changes(compiled_blocks, current_block_index)

        return block.generate_auto_reply(
            template_manager=template_manager,
            renderer_registry=renderer_registry,
            future_changes_map=future_changes_map,
            per_command_output_maximum_length=auto_reply_max_length,
        )

    def _calculate_future_changes(self, blocks: list, current_index: int) -> dict[int, int]:
        """Calculate how many times each section changes in future blocks."""
        future_changes_map: dict[int, int] = defaultdict(int)

        for future_block in blocks[current_index + 1 :]:
            if isinstance(future_block, AutoReply):
                for section_index, _ in future_block.dynamic_sections:
                    future_changes_map[section_index] += 1
            elif isinstance(future_block, InitialInterface):
                # InitialInterface blocks also count as changes for sections
                for section_index, _ in future_block.dynamic_sections:
                    future_changes_map[section_index] += 1

        return future_changes_map
