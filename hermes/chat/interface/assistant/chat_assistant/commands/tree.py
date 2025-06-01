import os
from collections.abc import Generator
from typing import Any

from hermes.chat.events import Event, MessageEvent
from hermes.chat.interface.assistant.chat_assistant.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.interface.helpers.cli_notifications import CLIColors
from hermes.chat.messages import LLMRunCommandOutput
from hermes.utils.file_extension import remove_quotes
from hermes.utils.tree_generator import TreeGenerator


class TreeCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Generate a directory tree structure."""

    def __init__(self):
        super().__init__(
            "tree",
            """Generate a directory tree structure.

This command shows the structure of files and directories starting from the given path.
You can optionally specify a maximum depth to limit how deep the tree will go.

If no path is provided, the current working directory will be used.
If no depth is specified, the complete tree will be generated.""",
        )
        self.add_section(
            "path",
            False,
            "Directory path to generate tree for (default: current directory)",
        )
        self.add_section("depth", False, "Maximum depth of the tree (default: full depth)")

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        if "path" not in args or not args["path"].strip():
            args["path"] = os.getcwd()
        else:
            args["path"] = remove_quotes(args["path"].strip())

        if "depth" in args and args["depth"].strip():
            try:
                args["depth"] = int(args["depth"].strip())
            except ValueError:
                args["depth"] = None
        else:
            args["depth"] = None
        return args

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        path = args["path"]
        depth = args["depth"]

        try:
            tree_generator = TreeGenerator()
            context.print_notification(f"Generating tree for: {path}")
            tree_string = tree_generator.generate_tree(path, depth)
            yield MessageEvent(LLMRunCommandOutput(text=tree_string, name="Directory Tree"))
            yield context.create_assistant_notification(f"Tree structure generated for path: {path}", "Directory Tree")
        except Exception as e:
            error_msg = f"Error generating tree for {path}: {str(e)}"
            context.print_notification(error_msg, CLIColors.RED)
            yield context.create_assistant_notification(error_msg, "Directory Tree Error")
