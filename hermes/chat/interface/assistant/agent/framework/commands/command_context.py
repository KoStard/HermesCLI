from abc import ABC, abstractmethod


class CommandContext(ABC):
    @abstractmethod
    def pop_engine_finish_signal(self) -> bool | None:
        """
        Retrieves and clears the signal indicating if the last focus-changing command
        determined that the engine should finish processing.
        Returns the signal (True if finish) or None if no signal was set.
        """
        pass

    @abstractmethod
    def pop_root_completion_message_signal(self) -> str | None:
        """
        Retrieves and clears the root completion message if the last focus-changing
        command produced one (e.g., when focusing up from the root node).
        Returns the message string or None if no message was set.
        """
        pass
