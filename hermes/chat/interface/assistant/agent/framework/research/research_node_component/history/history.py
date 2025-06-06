import json
import os
from pathlib import Path
from typing import Any

from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicSectionData
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.autoreply_aggregator import (
    AutoReplyAggregator,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
    HistoryBlock,
    InitialInterface,
)


class ResearchNodeHistory:
    """Manages the chat history for a research node"""

    def __init__(self, history_file_path: Path):
        self._compiled_blocks: list[HistoryBlock] = []
        self._auto_reply_aggregator = AutoReplyAggregator()
        self._history_file_path = history_file_path

        # Load history if file exists
        if os.path.exists(history_file_path):
            self.load()

    def add_message(self, author: str, content: str) -> None:
        """Add a message to the history"""
        self._compiled_blocks.append(ChatMessage(author=author, content=content))
        self.save()

    def get_compiled_blocks(self) -> list:
        """Get all blocks in the history"""
        return self._compiled_blocks.copy()

    def get_auto_reply_aggregator(self) -> AutoReplyAggregator:
        """Get the auto-reply aggregator for this history"""
        return self._auto_reply_aggregator

    def set_initial_interface_content(self, static_content: str, dynamic_data: list[DynamicSectionData]) -> None:
        """Set the initial interface content as an InitialInterface block"""
        # Create dynamic sections list with indices
        dynamic_sections = [(i, data) for i, data in enumerate(dynamic_data)]

        # Create InitialInterface block
        initial_block = InitialInterface(static_content, dynamic_sections)

        # Insert at the beginning if no initial interface exists yet
        if not self._has_initial_interface():
            self._compiled_blocks.insert(0, initial_block)
            self.save()

    def get_initial_interface_content(self) -> str | None:
        """Get the initial interface content - for backward compatibility, returns None if using new system"""
        # Return None to indicate we're using the new InitialInterface block system
        return None

    def _has_initial_interface(self) -> bool:
        """Check if an InitialInterface block already exists"""
        return len(self._compiled_blocks) > 0 and isinstance(self._compiled_blocks[0], InitialInterface)

    def prepare_and_add_auto_reply_block(self) -> None:
        """
        Compiles the current aggregator data into an AutoReply block, adds it
        to the history, but does NOT save or clear the aggregator.
        This is part of a transactional process.
        """
        if self._auto_reply_aggregator.is_empty():
            return

        # Create the auto-reply block without clearing the aggregator
        auto_reply = self._auto_reply_aggregator.compile()

        # Add to history blocks to be included in the next LLM prompt
        self._compiled_blocks.append(auto_reply)

    def rollback_last_auto_reply(self) -> None:
        """
        Removes the last block from history if it's an AutoReply.
        Used to roll back a transaction if the LLM call fails.
        """
        if self._compiled_blocks and isinstance(self._compiled_blocks[-1], AutoReply):
            self._compiled_blocks.pop()

    def commit_llm_turn(self, llm_response_content: str) -> None:
        """
        Finalizes the transaction by clearing the aggregator and saving the
        history, optionally adding the LLM response message first.
        """
        self._auto_reply_aggregator.clear()

        # add_message saves, so this covers saving the whole transaction.
        self.add_message("assistant", llm_response_content)

    def save(self) -> None:
        """Save history to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._history_file_path), exist_ok=True)

            # Serialize history blocks
            serialized_data = {
                "blocks": self._serialize_blocks(self._compiled_blocks),
                "auto_reply_aggregator": self._auto_reply_aggregator.serialize(),
            }

            # Write to file with pretty formatting
            with open(self._history_file_path, "w", encoding="utf-8") as file:
                json.dump(serialized_data, file, indent=2)

        except Exception as e:
            print(f"Error saving history: {e}")

    def load(self) -> None:
        """Load history from file"""
        try:
            if os.path.exists(self._history_file_path):
                with open(self._history_file_path, encoding="utf-8") as file:
                    data = json.load(file)

                    # Deserialize blocks
                    self._compiled_blocks = self._deserialize_blocks(data.get("blocks", []))

                    # Deserialize auto-reply aggregator state
                    aggregator_data = data.get("auto_reply_aggregator")
                    if aggregator_data:
                        self._auto_reply_aggregator.deserialize(aggregator_data)
        except Exception as e:
            print(f"Error loading history: {e}")

    def _serialize_blocks(self, blocks: list[HistoryBlock]) -> list[dict[str, Any]]:
        """Serialize history blocks to JSON-compatible format"""
        serialized = []

        for block in blocks:
            if isinstance(block, ChatMessage):
                serialized.append({"type": "ChatMessage", "author": block.author, "content": block.content})
            elif isinstance(block, InitialInterface):
                # Serialize InitialInterface block
                dynamic_sections = []
                if block.dynamic_sections:
                    for idx, section_data in block.dynamic_sections:
                        dynamic_sections.append({"index": idx, "section_data": section_data.serialize() if section_data else None})

                serialized.append(
                    {
                        "type": "InitialInterface",
                        "static_content": block.static_content,
                        "dynamic_sections": dynamic_sections,
                    }
                )
            elif isinstance(block, AutoReply):
                # For AutoReply, we need proper serialization of dynamic sections
                dynamic_sections = []
                if block.dynamic_sections:
                    for idx, section_data in block.dynamic_sections:
                        # Use the DynamicSectionData serialization method
                        dynamic_sections.append({"index": idx, "section_data": section_data.serialize() if section_data else None})

                # Use jsonpickle for command_outputs to handle complex nested structures
                import jsonpickle

                serialized.append(
                    {
                        "type": "AutoReply",
                        "error_report": block.error_report,
                        "command_outputs": jsonpickle.encode(block.command_outputs),
                        "messages": block.messages,
                        "confirmation_request": block.confirmation_request,
                        "dynamic_sections": dynamic_sections,
                    }
                )

        return serialized

    def _deserialize_blocks(self, serialized_blocks: list[dict[str, Any]]) -> list[HistoryBlock]:
        """Deserialize history blocks from JSON data"""
        blocks = []
        import jsonpickle

        for block_data in serialized_blocks:
            block_type = block_data.get("type")

            if block_type == "ChatMessage":
                blocks.append(ChatMessage(author=block_data.get("author", ""), content=block_data.get("content", "")))
            elif block_type == "InitialInterface":
                # Deserialize InitialInterface block
                dynamic_sections = []
                for section_data in block_data.get("dynamic_sections", []):
                    idx = section_data.get("index")
                    serialized_section = section_data.get("section_data")

                    if idx is not None and serialized_section:
                        deserialized_section = DynamicSectionData.deserialize(serialized_section)
                        if deserialized_section:
                            dynamic_sections.append((idx, deserialized_section))

                blocks.append(
                    InitialInterface(
                        static_content=block_data.get("static_content", ""),
                        dynamic_sections=dynamic_sections,
                    )
                )
            elif block_type == "AutoReply":
                # Deserialize dynamic sections
                dynamic_sections = []
                for section_data in block_data.get("dynamic_sections", []):
                    idx = section_data.get("index")
                    serialized_section = section_data.get("section_data")

                    if idx is not None and serialized_section:
                        # Use the DynamicSectionData deserialization method
                        deserialized_section = DynamicSectionData.deserialize(serialized_section)
                        if deserialized_section:
                            dynamic_sections.append((idx, deserialized_section))

                # Use jsonpickle to decode command outputs
                command_outputs = []
                try:
                    command_outputs_str = block_data.get("command_outputs", "[]")
                    command_outputs = jsonpickle.decode(command_outputs_str)
                except Exception as e:
                    print(f"Error decoding command outputs: {e}")

                blocks.append(
                    AutoReply(
                        error_report=block_data.get("error_report", ""),
                        command_outputs=command_outputs,
                        messages=block_data.get("messages", []),
                        confirmation_request=block_data.get("confirmation_request"),
                        dynamic_sections=dynamic_sections,
                    )
                )

        return blocks
