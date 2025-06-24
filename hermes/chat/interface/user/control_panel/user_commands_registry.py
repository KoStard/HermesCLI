from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.user.control_panel.commands import (
    agent_mode_command,
    audio_command,
    budget_command,
    clear_command,
    exa_url_command,
    exit_command,
    focus_subproblem_command,
    fuzzy_select_command,
    image_command,
    image_url_command,
    import_knowledgebase_command,
    list_assistant_commands_command,
    list_research_command,
    llm_commands_execution_command,
    load_history_command,
    once_command,
    pdf_command,
    print_research_status,
    save_history_command,
    set_assistant_command_status_command,
    switch_research_command,
    text_command,
    textual_file_command,
    textual_files_command,
    thinking_tokens_command,
    tree_command,
    url_command,
    video_command,
)


class UserCommandsRegistry:
    def __init__(
        self,
        *,
        extra_commands: list[ControlPanelCommand] | None = None,
    ):
        self.commands: dict[str, ControlPanelCommand] = {}
        self._register_all_commands(extra_commands)

    def _register_command(self, command: ControlPanelCommand) -> None:
        self.commands[command.command_label] = command

    def _register_all_commands(self, extra_commands: list[ControlPanelCommand] | None = None) -> None:
        self._register_command(agent_mode_command.register())
        self._register_command(audio_command.register())
        self._register_command(budget_command.register())
        self._register_command(clear_command.register())
        self._register_command(exa_url_command.register())
        self._register_command(exit_command.register())
        self._register_command(focus_subproblem_command.register())
        self._register_command(fuzzy_select_command.register())
        self._register_command(image_command.register())
        self._register_command(image_url_command.register())
        self._register_command(import_knowledgebase_command.register())
        self._register_command(list_assistant_commands_command.register())
        self._register_command(list_research_command.register())
        self._register_command(llm_commands_execution_command.register())
        self._register_command(load_history_command.register())
        self._register_command(once_command.register())
        self._register_command(pdf_command.register())
        self._register_command(save_history_command.register())
        self._register_command(set_assistant_command_status_command.register())
        self._register_command(switch_research_command.register())
        self._register_command(text_command.register())
        self._register_command(textual_file_command.register())
        self._register_command(textual_files_command.register())
        self._register_command(thinking_tokens_command.register())
        self._register_command(tree_command.register())
        self._register_command(url_command.register())
        self._register_command(video_command.register())
        self._register_command(print_research_status.register())

        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def get_command(self, command_label: str) -> ControlPanelCommand | None:
        return self.commands.get(command_label)

    def get_all_commands(self) -> list[str]:
        return list(self.commands.keys())

    def get_commands_dict(self) -> dict[str, ControlPanelCommand]:
        return self.commands
