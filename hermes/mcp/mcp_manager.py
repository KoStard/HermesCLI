import asyncio
import json
import logging
import threading
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from hermes.chat.interface.commands.command import Command
from hermes.mcp.mcp_client import McpClient

if TYPE_CHECKING:
    from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter

logger = logging.getLogger(__name__)


class McpManager:
    def __init__(
        self,
        chat_mcp_servers: dict[str, dict[str, Any] | str],
        deep_research_mcp_servers: dict[str, dict[str, Any] | str],
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
        chat_tasks = [self._create_and_start_client(name, config, self.chat_clients) for name, config in self.chat_servers_config.items()]
        dr_tasks = [
            self._create_and_start_client(name, config, self.deep_research_clients)
            for name, config in self.deep_research_servers_config.items()
        ]
        await asyncio.gather(*chat_tasks, *dr_tasks)
        self.initial_load_complete = True
        logger.info("Finished loading all MCP clients.")

    async def _create_and_start_client(self, name: str, config: dict | str, client_list: list[McpClient]):
        client = McpClient(name, config, self.loop)
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
        from hermes.chat.events import Event
        from hermes.mcp.mcp_client import McpError

        name = tool_schema.get("name", "unknown_mcp_tool")
        description = tool_schema.get("description", "An MCP-based tool.")
        help_text = f"MCP Tool: {name}\n\n{description}"
        loop = self.loop

        def _parse_tool_args(args: dict[str, Any]) -> dict[str, Any]:
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
            return tool_args

        def _call_tool_and_get_output(tool_args: dict[str, Any]) -> str:
            try:
                future = asyncio.run_coroutine_threadsafe(client.call_tool(name, tool_args), loop)
                result = future.result(timeout=60)

                content_parts = []
                if isinstance(result, dict) and "content" in result:
                    for content_item in result.get("content", []):
                        if content_item.get("type") == "text":
                            content_parts.append(content_item.get("text", ""))
                elif isinstance(result, str):
                    content_parts.append(result)
                elif result is not None:
                    content_parts.append(json.dumps(result, indent=2))

                output = "\n".join(content_parts)
                if not output and result is None:
                    return f"Tool '{name}' executed successfully with no output."
                return output

            except McpError as e:
                return f"MCP Tool Error from '{name}':\n{e.message}"
            except asyncio.TimeoutError:
                return f"Error: MCP tool '{name}' timed out after 60 seconds."
            except Exception as e:
                logger.error(f"Unexpected error calling MCP tool '{name}': {e}", exc_info=True)
                return f"Error: An unexpected error occurred while running command '{name}'."

        if mode == "chat":

            class McpChatToolCommand(Command[Any, Generator[Event, None, None]]):
                def execute(self, context: Any, args: dict[str, Any]) -> Generator[Event, None, None]:
                    tool_args = _parse_tool_args(args)
                    output = _call_tool_and_get_output(tool_args)

                    if hasattr(context, "create_assistant_notification"):
                        yield context.create_assistant_notification(f"MCP Tool '{name}' output:\n{output}")
                    else:
                        logger.warning(f"MCP chat command context for '{name}' is missing create_assistant_notification.")
                        # Fallback for contexts like DebugInterface that might not have the notification method
                        if hasattr(context, "print_notification"):
                            context.print_notification(f"MCP Tool '{name}' output:\n{output}")

            command = McpChatToolCommand(name, help_text)
        else:  # deep_research

            class McpDeepResearchToolCommand(Command[Any, None]):
                def execute(self, context: Any, args: dict[str, Any]) -> None:
                    tool_args = _parse_tool_args(args)
                    output = _call_tool_and_get_output(tool_args)
                    if hasattr(context, "add_command_output"):
                        context.add_command_output(name, args, output)
                    else:
                        logger.warning(f"MCP deep_research command context for '{name}' is missing add_command_output.")

            command = McpDeepResearchToolCommand(name, help_text)

        # Configure the command sections based on the tool's input schema
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # Check if we should use a single json blob for arguments
        has_complex_arg = any(prop.get("type") in ["object", "array"] for prop in properties.values())

        if has_complex_arg:
            # For simplicity, if any argument is complex, we ask for all arguments in a single JSON blob.
            is_data_json_required = any(prop_name in required for prop_name in properties.keys())
            command.add_section("data_json", is_data_json_required, "All tool arguments as a single JSON object.")
        else:
            # All arguments are simple types (string, number, etc.)
            for prop_name, prop_details in properties.items():
                is_required = prop_name in required
                prop_description = prop_details.get("description", "")
                command.add_section(prop_name, is_required, prop_description)

        return command
