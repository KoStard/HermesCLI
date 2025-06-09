from typing import TYPE_CHECKING

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode


class SubproblemSelector:
    """Interactive TUI for selecting subproblems from the research tree."""

    def __init__(self, root_node: "ResearchNode"):
        self.root_node = root_node
        self.nodes = self._collect_all_nodes(root_node)
        self.selected_index = 0
        self.result = None

    def _collect_all_nodes(self, node: "ResearchNode", level: int = 0) -> list[tuple["ResearchNode", int, str]]:
        """Collect all nodes from the tree with their display information."""
        nodes = []

        # Add current node
        prefix = "  " * level
        if level == 0:
            display_name = f"{prefix}🏠 {node.get_title()} (Root)"
        else:
            status_icon = self._get_status_icon(node)
            display_name = f"{prefix}{status_icon} {node.get_title()}"

        nodes.append((node, level, display_name))

        # Add child nodes recursively
        for child in node.list_child_nodes():
            nodes.extend(self._collect_all_nodes(child, level + 1))

        return nodes

    def _get_status_icon(self, node: "ResearchNode") -> str:
        """Get status icon for a node."""
        status = node.get_problem_status()
        status_map = {
            "READY_TO_START": "🟡",
            "IN_PROGRESS": "🔵",
            "FINISHED": "✅",
            "FAILED": "❌",
            "CANCELLED": "⏹️",
            "PENDING": "⏳",
        }
        return status_map.get(status.name if hasattr(status, 'name') else str(status), "⚪")

    def _get_display_text(self):
        """Generate the display text for the selector."""
        lines = []
        lines.append("Select a subproblem to focus on:")
        lines.append("")

        for i, (_, _, display_name) in enumerate(self.nodes):
            if i == self.selected_index:
                lines.append(f"❯ {display_name}")
            else:
                lines.append(f"  {display_name}")

        lines.append("")
        lines.append("Use ↑/↓ to navigate, Enter to select, Esc to cancel")

        return "\n".join(lines)

    def select_subproblem(self) -> "ResearchNode | None":
        """Show the selector and return the selected node."""
        kb = self._create_key_bindings()
        style = self._create_style()
        layout = self._create_layout()

        app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=False,
        )

        app.run()
        return self.result

    def _create_key_bindings(self) -> KeyBindings:
        """Create keyboard bindings for the selector."""
        kb = KeyBindings()
        self._register_navigation_keys(kb)
        self._register_action_keys(kb)
        return kb

    def _register_navigation_keys(self, kb: KeyBindings):
        """Register navigation key bindings."""
        @kb.add("up")
        def move_up(event):
            if self.selected_index > 0:
                self.selected_index -= 1

        @kb.add("down")
        def move_down(event):
            if self.selected_index < len(self.nodes) - 1:
                self.selected_index += 1

    def _register_action_keys(self, kb: KeyBindings):
        """Register action key bindings."""
        @kb.add("enter")
        def select(event):
            self.result = self.nodes[self.selected_index][0]
            event.app.exit()

        @kb.add("escape")
        @kb.add("c-c")
        def cancel(event):
            self.result = None
            event.app.exit()

    def _create_style(self) -> Style:
        """Create the visual style for the selector."""
        return Style.from_dict({
            "title": "#ffffff bold",
            "selection": "#00aa00 bold",
            "normal": "#ffffff",
        })

    def _create_layout(self) -> Layout:
        """Create the layout for the selector."""
        return Layout(
            HSplit([
                Window(
                    FormattedTextControl(lambda: self._get_display_text()),
                    height=len(self.nodes) + 5,
                    wrap_lines=True,
                )
            ])
        )
