import asyncio
import json
import logging
import shlex
from asyncio import StreamReader, StreamWriter
from typing import Any

logger = logging.getLogger(__name__)


class McpError(Exception):
    def __init__(self, error_obj):
        self.code = error_obj.get("code")
        self.message = error_obj.get("message")
        self.data = error_obj.get("data")
        super().__init__(f"MCP Error {self.code}: {self.message}")


class McpClient:
    def __init__(self, name: str, command: str, loop: asyncio.AbstractEventLoop):
        self.name = name
        self.command = command
        self.loop = loop
        self.process: asyncio.subprocess.Process | None = None
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None
        self.request_id = 0
        self.futures: dict[int, asyncio.Future] = {}
        self.tools: list[dict] = []
        self.status = "disconnected"
        self.error_message: str | None = None

    async def start(self):
        self.status = "connecting"
        try:
            cmd_parts = shlex.split(self.command)
            self.process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.reader = self.process.stdout
            self.writer = self.process.stdin
            asyncio.create_task(self._read_output())
            asyncio.create_task(self._read_stderr())
            await self._initialize()
            self.status = "connected"
            logger.info(f"MCP client '{self.name}' connected successfully.")
        except Exception as e:
            self.status = "error"
            self.error_message = f"Failed to start or initialize MCP server '{self.name}': {e}"
            logger.error(self.error_message)

    async def _read_output(self):
        if not self.reader:
            return
        while not self.reader.at_eof():
            line = await self.reader.readline()
            if not line:
                break
            try:
                message = json.loads(line)
                if "id" in message and message["id"] in self.futures:
                    future = self.futures.pop(message["id"])
                    if "error" in message:
                        future.set_exception(McpError(message["error"]))
                    else:
                        future.set_result(message.get("result"))
                else:
                    logger.debug(f"Received unhandled message from {self.name}: {message}")
            except json.JSONDecodeError:
                logger.warning(f"MCP client {self.name}: Received non-JSON message: {line.decode().strip()}")

    async def _read_stderr(self):
        if not self.process or not self.process.stderr:
            return
        while not self.process.stderr.at_eof():
            line_bytes = await self.process.stderr.readline()
            if not line_bytes:
                break
            line = line_bytes.decode().strip()
            logger.debug(f"MCP server '{self.name}' stderr: {line}")
            if "[error]" in line.lower() and self.status != "error":  # Capture first error
                self.status = "error"
                self.error_message = f"Error from server '{self.name}': {line}"

    async def _send_request(self, method: str, params: dict | None = None) -> Any:
        if not self.writer:
            raise ConnectionError(f"MCP client '{self.name}' is not connected.")
        self.request_id += 1
        req_id = self.request_id
        request = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        future = self.loop.create_future()
        self.futures[req_id] = future

        self.writer.write(json.dumps(request).encode() + b"\n")
        await self.writer.drain()

        return await asyncio.wait_for(future, timeout=30.0)

    async def _initialize(self):
        init_params = {
            "protocolVersion": "2025-03-26",
            "clientInfo": {"name": "hermes", "version": "0.1.0"},
            "capabilities": {},
        }
        await self._send_request("initialize", init_params)

        initialized_notification = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        if not self.writer:
            raise ConnectionError(f"MCP client '{self.name}' is not connected.")
        self.writer.write(json.dumps(initialized_notification).encode() + b"\n")
        await self.writer.drain()

        await self._load_tools()

    async def _load_tools(self):
        response = await self._send_request("tools/list")
        if response:
            self.tools = response.get("tools", [])
            logger.info(f"Loaded {len(self.tools)} tools from MCP server '{self.name}'")
        else:
            logger.warning(f"MCP server '{self.name}' returned no tools.")

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        return await self._send_request("tools/call", {"name": tool_name, "arguments": args})

    async def stop(self):
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except ProcessLookupError:
                pass
        self.status = "disconnected"
