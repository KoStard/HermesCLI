from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


class ExecutionState:
    _active_node: ResearchNode | None = None
    _should_finish: bool | None = None

    @property
    def has_active_node(self) -> bool:
        return self._active_node is not None

    @property
    def active_node(self) -> ResearchNode:
        if not self.has_active_node:
            raise ValueError("active_node accessed on execution state, while the node is not configured yet")
        assert self._active_node is not None  # Satisfy type checker
        return self._active_node

    def set_active_node(self, node: ResearchNode):
        self._active_node = node

    def load_rest_from(self, old_execution_state: 'ExecutionState'):
        if not self._active_node:
            self._active_node = old_execution_state._active_node

        if self._should_finish is None:
            self._should_finish = old_execution_state._should_finish

    def set_should_finish(self, should_finish: bool):
        self._should_finish = should_finish

    def should_finish(self) -> bool:
        return self._should_finish or False
