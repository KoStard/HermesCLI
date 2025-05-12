from typing import Any

from hermes.chat.interface.assistant.deep_research_assistant.engine.context.dynamic_sections import DynamicSectionData
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history_blocks import AutoReply


class AutoReplyAggregator:
    def __init__(self):
        self.error_reports: list[str] = []
        self.command_outputs: list[tuple[str, dict[str, Any]]] = []
        self.internal_messages: list[tuple[str, str]] = []
        self.confirmation_requests: list[str] = []
        # Stores the *data* objects for changed sections and their original index
        self.dynamic_sections_to_report: list[tuple[int, DynamicSectionData]] = []
        # Stores the last known state of *all* dynamic section data objects
        self.last_dynamic_sections_state: list[DynamicSectionData] = []

    def add_error_report(self, error_report: str):
        self.error_reports.append(error_report)

    def add_confirmation_request(self, message: str):
        self.confirmation_requests.append(message)

    def add_command_output(self, cmd_name: str, output_data: dict):
        self.command_outputs.append((cmd_name, output_data))

    def add_internal_message_from(self, message: str, origin_node_title: str):
        self.internal_messages.append((message, origin_node_title))

    def update_dynamic_sections(self, new_sections_data: list[DynamicSectionData]):
        """
        Compare new dynamic section data with the last known state and track changes.

        Args:
            new_sections_data: List of data objects for all current dynamic sections.
        """
        changed_sections_with_indices: list[tuple[int, DynamicSectionData]] = []

        # Ensure lengths match for comparison, handle initialization
        if not self.last_dynamic_sections_state:
            # First time seeing sections, consider all as 'changed' for the initial view,
            # but don't report them in the *first* auto-reply unless explicitly needed.
            # For simplicity now, just initialize the state. The first auto-reply won't
            # list "updated sections" unless something else triggers it.
            self.last_dynamic_sections_state = new_sections_data[:]  # Use slicing for a copy
        elif len(new_sections_data) != len(self.last_dynamic_sections_state):
            # This indicates a structural change (sections added/removed), which
            # the current design doesn't handle dynamically. Treat all as changed.
            # Or log an error/warning. For now, assume fixed structure.
            print("Warning: Number of dynamic sections changed. Re-evaluating all.")
            for i, data_instance in enumerate(new_sections_data):
                # Check against old state if index exists, otherwise it's new/changed
                if i >= len(self.last_dynamic_sections_state) or data_instance != self.last_dynamic_sections_state[i]:
                    changed_sections_with_indices.append((i, data_instance))
        else:
            # Compare data objects element-wise using dataclass equality (__eq__)
            for i, current_data in enumerate(new_sections_data):
                if current_data != self.last_dynamic_sections_state[i]:
                    changed_sections_with_indices.append((i, current_data))

        # Store the changed sections (data + index) to be included in the *next* auto-reply
        self.dynamic_sections_to_report = changed_sections_with_indices

        # Update the last known state for *all* sections
        self.last_dynamic_sections_state = new_sections_data[:]  # Use slicing for a copy

    def clear(self):
        self.error_reports = []
        self.command_outputs = []
        self.internal_messages = []
        self.confirmation_requests = []
        self.dynamic_sections_to_report = []
        # Keep last_dynamic_sections_state for comparison

    def is_empty(self):
        """Check if there's anything to report in the auto-reply."""
        return (
            not self.error_reports
            and not self.command_outputs
            and not self.internal_messages
            and not self.confirmation_requests
            and not self.dynamic_sections_to_report  # Check the changed sections list
        )

    def compile_and_clear(self) -> AutoReply:
        error_report = "\n".join(self.error_reports)
        confirmation_request = "\n".join(self.confirmation_requests) if self.confirmation_requests else None
        auto_reply = AutoReply(
            error_report,
            self.command_outputs,
            self.internal_messages,
            confirmation_request,
            self.dynamic_sections_to_report,  # Pass the changed sections data
        )
        self.clear()  # Clears reports, outputs, messages, requests, and changed sections list
        return auto_reply

    def serialize(self) -> dict[str, Any]:
        """Serialize the aggregator state"""
        import jsonpickle

        # Fully serialize dynamic sections using their serialization methods
        dynamic_sections = []
        for idx, section_data in self.dynamic_sections_to_report:
            dynamic_sections.append({
                "index": idx,
                "section_data": section_data.serialize() if section_data else None
            })

        last_sections_state = []
        for data in self.last_dynamic_sections_state:
            if data:
                last_sections_state.append(data.serialize())

        return {
            "error_reports": self.error_reports,
            "command_outputs": jsonpickle.encode(self.command_outputs),
            "internal_messages": self.internal_messages,
            "confirmation_requests": self.confirmation_requests,
            "dynamic_sections_to_report": dynamic_sections,
            "last_dynamic_sections_state": last_sections_state
        }

    def deserialize(self, data: dict[str, Any]) -> None:
        """Deserialize aggregator state from JSON data"""
        import jsonpickle

        self.error_reports = data.get("error_reports", [])

        # Deserialize command outputs with jsonpickle
        try:
            command_outputs_data = data.get("command_outputs", "[]")
            self.command_outputs = jsonpickle.decode(command_outputs_data)
        except Exception as e:
            print(f"Error decoding command outputs in aggregator: {e}")
            self.command_outputs = []

        self.internal_messages = data.get("internal_messages", [])
        self.confirmation_requests = data.get("confirmation_requests", [])

        # Restore dynamic sections using DynamicSectionData deserialization
        self.dynamic_sections_to_report = []
        dynamic_sections_data = data.get("dynamic_sections_to_report", [])
        for section in dynamic_sections_data:
            idx = section.get("index")
            serialized_section = section.get("section_data")

            if idx is not None and serialized_section:
                deserialized_section = DynamicSectionData.deserialize(serialized_section)
                if deserialized_section:
                    self.dynamic_sections_to_report.append((idx, deserialized_section))

        # Restore last dynamic sections state
        self.last_dynamic_sections_state = []
        for serialized_section in data.get("last_sections_state", []):
            if serialized_section:
                deserialized_section = DynamicSectionData.deserialize(serialized_section)
                if deserialized_section:
                    self.last_dynamic_sections_state.append(deserialized_section)
