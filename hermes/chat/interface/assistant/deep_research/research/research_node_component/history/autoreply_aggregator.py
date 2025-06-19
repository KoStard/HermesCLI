from typing import Any

from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData
from hermes.chat.interface.assistant.deep_research.research.research_node_component.history.history_blocks import AutoReply


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

    def _initialize_dynamic_sections(self, new_sections_data: list[DynamicSectionData]):
        """Initialize the dynamic sections state for first-time use."""
        self.last_dynamic_sections_state = new_sections_data[:]  # Use slicing for a copy
        self.dynamic_sections_to_report = []  # No changes to report on first init

    def _detect_structural_changes(self, new_sections_data: list[DynamicSectionData]) -> list[tuple[int, DynamicSectionData]]:
        """Handle the case where the number of sections has changed."""
        changed_sections = []
        print("Warning: Number of dynamic sections changed. Re-evaluating all.")
        for i, data_instance in enumerate(new_sections_data):
            if i >= len(self.last_dynamic_sections_state) or data_instance != self.last_dynamic_sections_state[i]:
                changed_sections.append((i, data_instance))
        return changed_sections

    def _detect_content_changes(self, new_sections_data: list[DynamicSectionData]) -> list[tuple[int, DynamicSectionData]]:
        """Compare data objects element-wise to detect content changes."""
        changed_sections = []
        for i, current_data in enumerate(new_sections_data):
            if current_data != self.last_dynamic_sections_state[i]:
                changed_sections.append((i, current_data))
        return changed_sections

    def set_initial_dynamic_interface(self, dynamic_sections: list[tuple[int, DynamicSectionData]]):
        if not self.last_dynamic_sections_state:
            self.last_dynamic_sections_state = [data for _, data in dynamic_sections]

    def update_dynamic_sections(self, new_sections_data: list[DynamicSectionData]):
        """Compare new dynamic section data with the last known state and track changes.

        Args:
            new_sections_data: List of data objects for all current dynamic sections.
        """
        # Handle first-time initialization
        if not self.last_dynamic_sections_state:
            self._initialize_dynamic_sections(new_sections_data)
            return

        # Detect changes based on whether structure or just content changed
        if len(new_sections_data) != len(self.last_dynamic_sections_state):
            self.dynamic_sections_to_report = self._detect_structural_changes(new_sections_data)
        else:
            self.dynamic_sections_to_report = self._detect_content_changes(new_sections_data)

        # Update the last known state for all sections
        self.last_dynamic_sections_state = new_sections_data[:]

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

    def compile(self) -> AutoReply:
        """Compiles aggregated data into an AutoReply object without clearing."""
        error_report = "\n".join(self.error_reports)
        confirmation_request = "\n".join(self.confirmation_requests) if self.confirmation_requests else None
        return AutoReply(
            error_report,
            self.command_outputs,
            self.internal_messages,
            confirmation_request,
            self.dynamic_sections_to_report,  # Pass the changed sections data
        )

    def serialize(self) -> dict[str, Any]:
        """Serialize the aggregator state"""
        import jsonpickle

        # Fully serialize dynamic sections using their serialization methods
        dynamic_sections = []
        for idx, section_data in self.dynamic_sections_to_report:
            dynamic_sections.append({"index": idx, "section_data": section_data.serialize() if section_data else None})

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
            "last_dynamic_sections_state": last_sections_state,
        }

    def _deserialize_command_outputs(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        """Helper method to deserialize command outputs from JSON data"""
        import jsonpickle

        try:
            command_outputs_data = data.get("command_outputs", "[]")
            return jsonpickle.decode(command_outputs_data)
        except Exception as e:
            print(f"Error decoding command outputs in aggregator: {e}")
            return []

    def _deserialize_dynamic_sections(self, sections_data: list[dict[str, Any]]) -> list[tuple[int, DynamicSectionData]]:
        """Helper method to deserialize dynamic sections data"""
        result = []
        for section in sections_data:
            idx = section.get("index")
            serialized_section = section.get("section_data")

            if idx is not None and serialized_section:
                deserialized_section = DynamicSectionData.deserialize(serialized_section)
                if deserialized_section:
                    result.append((idx, deserialized_section))
        return result

    def _deserialize_last_sections_state(self, sections_data: list[dict[str, Any]]) -> list[DynamicSectionData]:
        """Helper method to deserialize the last sections state"""
        result = []
        for serialized_section in sections_data:
            if serialized_section:
                deserialized_section = DynamicSectionData.deserialize(serialized_section)
                if deserialized_section:
                    result.append(deserialized_section)
        return result

    def deserialize(self, data: dict[str, Any]) -> None:
        """Deserialize aggregator state from JSON data"""
        # Basic properties
        self.error_reports = data.get("error_reports", [])
        self.internal_messages = data.get("internal_messages", [])
        self.confirmation_requests = data.get("confirmation_requests", [])

        # Complex properties that need special handling
        self.command_outputs = self._deserialize_command_outputs(data)
        self.dynamic_sections_to_report = self._deserialize_dynamic_sections(
            data.get("dynamic_sections_to_report", []),
        )
        self.last_dynamic_sections_state = self._deserialize_last_sections_state(
            data.get("last_sections_state", []),
        )
