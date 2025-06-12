import asyncio
import json
import logging
import threading
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from hermes.chat.interface.commands.command import Command
from hermes.json_config_manager import JsonConfigManager
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
        self.config_manager = JsonConfigManager()  # Used for tool configuration access

        # Store server tool configurations
        self.chat_server_tool_configs: dict[str, dict[str, bool]] = {}
        self.deep_research_server_tool_configs: dict[str, dict[str, bool]] = {}

        # Initialize tool configurations
        for server_name, server_config in chat_mcp_servers.items():
            self.chat_server_tool_configs[server_name] = self.config_manager.get_mcp_server_tool_config(server_name, server_config)

        for server_name, server_config in deep_research_mcp_servers.items():
            self.deep_research_server_tool_configs[server_name] = self.config_manager.get_mcp_server_tool_config(server_name, server_config)

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
        if mode == "chat":
            clients = self.chat_clients
            server_tool_configs = self.chat_server_tool_configs
        else:  # deep_research mode
            clients = self.deep_research_clients
            server_tool_configs = self.deep_research_server_tool_configs

        for client in clients:
            if client.status != "connected":
                print("Skipping MCP client, as it's not connected", client)
                continue

            # Get tool configuration for this client
            tool_config = server_tool_configs.get(client.name, {})

            for tool_schema in client.tools:
                tool_name = tool_schema.get("name", "unknown_mcp_tool")

                # Check if this tool is enabled
                # If tool_config is empty, all tools are enabled (default behavior)
                # Otherwise, check if the tool is explicitly enabled or not mentioned (default to disabled)
                if not tool_config or tool_config.get(tool_name, False):
                    commands.append(self._create_command_from_schema(client, tool_schema, mode))
                else:
                    logger.debug(f"Skipping disabled MCP tool '{tool_name}' from server '{client.name}'")

        return commands

    def _parse_tool_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Parse command arguments, handling both direct args and JSON blob."""
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

    def _create_command_from_schema(self, client: McpClient, tool_schema: dict, mode: str) -> Command:
        name = tool_schema.get("name", "unknown_mcp_tool")
        description = tool_schema.get("description", "An MCP-based tool.")
        help_text = f"MCP Tool: {name}\n\n{description}"

        if mode == "chat":
            command = self._create_chat_command(client, name, help_text)
        else:  # deep_research
            command = self._create_deep_research_command(client, name, help_text)

        # Configure command sections
        self._configure_command_sections(command, tool_schema)

        return command

    def _execute_tool_call(self, client: McpClient, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Execute the tool call and return the raw result."""
        future = asyncio.run_coroutine_threadsafe(client.call_tool(tool_name, tool_args), self.loop)
        return future.result(timeout=60)

    def _extract_text_content(self, result_dict: dict) -> list[str]:
        """Extract text content from a dictionary result format."""
        content_parts = []
        for content_item in result_dict.get("content", []):
            if content_item.get("type") == "text":
                content_parts.append(content_item.get("text", ""))
        return content_parts

    def _format_non_dict_result(self, result: Any) -> list[str]:
        """Format non-dictionary results."""
        if isinstance(result, str):
            return [result]
        if result is not None:
            return [json.dumps(result, indent=2)]
        return []

    def _create_output_message(self, tool_name: str, content_parts: list[str], result: Any) -> str:
        """Create the final output message from content parts."""
        output = "\n".join(content_parts)
        if not output and result is None:
            return f"Tool '{tool_name}' executed successfully with no output."
        return output

    def _format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format the tool result into a string output."""
        if isinstance(result, dict) and "content" in result:
            content_parts = self._extract_text_content(result)
        else:
            content_parts = self._format_non_dict_result(result)

        return self._create_output_message(tool_name, content_parts, result)

    def _call_tool_and_get_output(self, client: McpClient, tool_name: str, tool_args: dict[str, Any]) -> str:
        """Call the tool with arguments and return formatted output or error message."""
        from hermes.mcp.mcp_client import McpError

        try:
            result = self._execute_tool_call(client, tool_name, tool_args)
            return self._format_tool_result(tool_name, result)
        except McpError as e:
            return f"MCP Tool Error from '{tool_name}':\n{e.message}"
        except asyncio.TimeoutError:
            return f"Error: MCP tool '{tool_name}' timed out after 60 seconds."
        except Exception as e:
            logger.error(f"Unexpected error calling MCP tool '{tool_name}': {e}", exc_info=True)
            return f"Error: An unexpected error occurred while running command '{tool_name}'."

    def _create_chat_command(self, client: McpClient, tool_name: str, help_text: str) -> Command:
        """Create a command for chat assistant mode."""
        from hermes.chat.events import Event

        class McpChatToolCommand(Command[Any, Generator[Event, None, None]]):
            def execute(tool_self, context: Any, args: dict[str, Any]) -> Generator[Event, None, None]:  # noqa: N805
                tool_args = self._parse_tool_args(args)
                output = self._call_tool_and_get_output(client, tool_name, tool_args)

                if hasattr(context, "create_assistant_notification"):
                    yield context.create_assistant_notification(f"MCP Tool '{tool_name}' output:\n{output}")
                else:
                    logger.warning(f"MCP chat command context for '{tool_name}' is missing create_assistant_notification.")
                    # Fallback for contexts like DebugInterface that might not have the notification method
                    if hasattr(context, "print_notification"):
                        context.print_notification(f"MCP Tool '{tool_name}' output:\n{output}")

        # Need to bind instance methods to the command class instance
        cmd = McpChatToolCommand(tool_name, help_text)
        cmd.execute.__globals__["self"] = self
        return cmd

    def _create_deep_research_command(self, client: McpClient, tool_name: str, help_text: str) -> Command:
        """Create a command for deep research mode."""

        class McpDeepResearchToolCommand(Command[Any, None]):
            def execute(tool_self, context: Any, args: dict[str, Any]) -> None:  # noqa: N805
                tool_args = self._parse_tool_args(args)
                output = self._call_tool_and_get_output(client, tool_name, tool_args)
                if hasattr(context, "add_command_output"):
                    context.add_command_output(tool_name, args, output)
                else:
                    logger.warning(f"MCP deep_research command context for '{tool_name}' is missing add_command_output.")

        # Need to bind instance methods to the command class instance
        cmd = McpDeepResearchToolCommand(tool_name, help_text)
        cmd.execute.__globals__["self"] = self
        return cmd

    def _configure_command_sections(self, command: Command, tool_schema: dict) -> None:
        """Configure the sections for a command based on tool schema."""
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # Check if we should use a single json blob for arguments
        has_complex_arg = any(prop.get("type") in ["object", "array"] for prop in properties.values())

        if has_complex_arg:
            # For simplicity, if any argument is complex, we ask for all arguments in a single JSON blob.
            is_data_json_required = any(prop_name in required for prop_name in properties)
            command.add_section("data_json", is_data_json_required, "All tool arguments as a single JSON object.")
        else:
            # All arguments are simple types (string, number, etc.)
            for prop_name, prop_details in properties.items():
                is_required = prop_name in required
                prop_description = prop_details.get("description", "")
                command.add_section(prop_name, is_required, prop_description)
