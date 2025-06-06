import asyncio
import json
import logging
import threading
from typing import TYPE_CHECKING, Any

from hermes.chat.interface.commands.command import Command
from hermes.mcp.mcp_client import McpClient

if TYPE_CHECKING:
    from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter

logger = logging.getLogger(__name__)


class McpManager:
    def __init__(
        self,
        chat_mcp_servers: dict[str, str],
        deep_research_mcp_servers: dict[str, str],
        notifications_printer: "CLINotificationsPrinter",
    ):
        self.chat_servers_config = chat_mcp_servers
        self.deep_research_servers_config = deep_research_mcp_servers
        self.notifications_printer = notifications_printer

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.chat_clients: list[McpClient] = []
        self.deep_research_clients: list[McpClient] = []
        self.initial_load_complete = False
        self._errors_acknowledged = False

    def start_loading(self):
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self._load_clients(), self.loop)

    async def _load_clients(self):
        logger.info("Starting MCP client loading in background.")
        chat_tasks = [
            self._create_and_start_client(name, cmd, self.chat_clients) for name, cmd in self.chat_servers_config.items()
        ]
        dr_tasks = [
            self._create_and_start_client(name, cmd, self.deep_research_clients)
            for name, cmd in self.deep_research_servers_config.items()
        ]
        await asyncio.gather(*chat_tasks, *dr_tasks)
        self.initial_load_complete = True
        logger.info("Finished loading all MCP clients.")

    async def _create_and_start_client(self, name: str, cmd: str, client_list: list[McpClient]):
        client = McpClient(name, cmd, self.loop)
        client_list.append(client)
        await client.start()

    def get_status_report(self) -> str | None:
        if self.initial_load_complete:
            if not self.has_errors() or self._errors_acknowledged:
                return None
            return self.get_error_report()

        report_parts = ["MCP Servers are loading..."]
        all_clients = self.chat_clients + self.deep_research_clients
        for client in all_clients:
            if client.status == "connecting":
                report_parts.append(f"  - {client.name}: Connecting...")

        return "\n".join(report_parts) if len(report_parts) > 1 else None

    def get_error_report(self) -> str:
        report_parts = ["MCP Server Errors:"]
        for client in self.chat_clients + self.deep_research_clients:
            if client.status == "error" and client.error_message:
                report_parts.append(f"  - {client.name}: {client.error_message}")
        return "\n".join(report_parts)

    def has_errors(self) -> bool:
        return any(client.status == "error" for client in self.chat_clients + self.deep_research_clients)

    def acknowledge_errors(self) -> None:
        self._errors_acknowledged = True

    def wait_for_initial_load(self, timeout: float = 30.0):
        """Wait until the initial loading of all MCP clients is complete."""
        import time

        logger.debug("Waiting for MCP clients to finish loading...")
        start_time = time.monotonic()
        while not self.initial_load_complete:
            if time.monotonic() - start_time > timeout:
                logger.warning(f"Timed out waiting for MCP clients to load after {timeout} seconds.")
                break
            time.sleep(0.1)
        if self.initial_load_complete:
            logger.debug("MCP clients finished loading.")

    def create_commands_for_mode(self, mode: str) -> list[Command]:
        commands = []
        clients = self.chat_clients if mode == "chat" else self.deep_research_clients
        for client in clients:
            if client.status != "connected":
                continue
            for tool_schema in client.tools:
                commands.append(self._create_command_from_schema(client, tool_schema, mode))
        return commands

    def _create_command_from_schema(self, client: McpClient, tool_schema: dict, mode: str) -> Command:
        name = tool_schema.get("name", "unknown_mcp_tool")
        description = tool_schema.get("description", "An MCP-based tool.")
        help_text = f"MCP Tool: {name}\n\n{description}"
        loop = self.loop

        # Define a concrete command class dynamically for each MCP tool.
        # This class will hold the logic to call the tool.
        class McpToolCommand(Command[Any, None]):
            def execute(self, context: Any, args: dict[str, Any]) -> None:
                """Execute the MCP tool call."""
                tool_args = {}
                if "data_json" in args:
                    try:
                        json_args = json.loads(args["data_json"])
                        tool_args.update(json_args)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON in data_json: {e}") from e

                for arg_name, arg_value in args.items():
                    if arg_name != "data_json":
                        tool_args[arg_name] = arg_value

                # The `client`, `name`, and `loop` are captured from the outer scope.
                future = asyncio.run_coroutine_threadsafe(client.call_tool(name, tool_args), loop)
                try:
                    result = future.result(timeout=60)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"MCP tool '{name}' timed out after 60 seconds.") from None

                output = ""
                if result.get("isError"):
                    output += f"MCP Tool Error from '{name}':\n"

                content_parts = []
                for content_item in result.get("content", []):
                    if content_item.get("type") == "text":
                        content_parts.append(content_item.get("text"))
                output += "\n".join(content_parts)

                # Route the output based on the mode (Chat vs. Deep Research)
                if mode == "chat" and hasattr(context, "print_notification"):
                    context.print_notification(f"MCP Tool '{name}' output:\n{output}")
                elif mode == "deep_research" and hasattr(context, "add_command_output"):
                    context.add_command_output(name, args, output)
                elif hasattr(context, "print_notification"):
                    # Fallback for other contexts that might have print_notification
                    context.print_notification(f"MCP Tool '{name}' output:\n{output}")
                else:
                    logger.warning(
                        f"MCP Tool '{name}' executed in mode '{mode}' but context has no known output method. Output: {output}"
                    )

        # Instantiate the concrete command class
        command = McpToolCommand(name, help_text)

        # Configure the command sections based on the tool's input schema
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        has_json_blob_arg = False

        for prop_details in properties.values():
            prop_type = prop_details.get("type", "string")
            # If the tool expects a complex object or array, we'll use a single JSON section
            if prop_type in ["object", "array"]:
                has_json_blob_arg = True
                continue

        if not has_json_blob_arg:
            for prop_name, prop_details in properties.items():
                is_required = prop_name in required
                prop_description = prop_details.get("description", "")
                command.add_section(prop_name, is_required, prop_description)

        if has_json_blob_arg:
            command.add_section("data_json", False, "JSON-structured arguments for this tool.")

        return command
