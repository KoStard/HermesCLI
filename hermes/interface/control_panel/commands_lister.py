from hermes.interface.control_panel import ControlPanelCommand


class CommandsLister:
    """Formats and prints command information"""

    def print_commands(self, commands: list[ControlPanelCommand]):
        """Print commands in a formatted table"""
        if not commands:
            print("No commands found.")
            return

        # Find maximum widths for formatting
        id_width = max(len(cmd.command_id) for cmd in commands)
        desc_width = max(len(cmd.short_description) for cmd in commands)

        # Print header
        print(f"{'Command ID':<{id_width}} | Description")
        print("-" * id_width + "-+-" + "-" * desc_width)

        # Print each command
        for cmd in sorted(commands, key=lambda x: x.command_id):
            print(f"{cmd.command_id:<{id_width}} | {cmd.short_description}")
