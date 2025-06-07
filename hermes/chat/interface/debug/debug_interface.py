import json
import os
import platform
import socket
import subprocess
import sys
from collections.abc import Generator

from hermes.chat.events import Event
from hermes.chat.interface.assistant.chat.control_panel import (
    ChatAssistantControlPanel,
)
from hermes.chat.interface.assistant.chat.assistant_orchestrator import ChatAssistantOrchestrator
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.messages import TextMessage


class DebugInterface(ChatAssistantOrchestrator):
    def __init__(
        self,
        control_panel: ChatAssistantControlPanel,
        model: ChatModel,
        port=12345,
    ):
        self.port = port
        self.socket = None
        self.connection = None
        self._spawn_debug_client()
        self._setup_server()
        super().__init__(model, control_panel)

    def _spawn_debug_client(self):
        system = platform.system()
        client_path = os.path.join(os.path.dirname(__file__), "debug_client.py")
        python_path = sys.executable

        if system == "Darwin":  # macOS
            cmd = f"""osascript -e 'tell app "Terminal" to do script "{python_path} {client_path} --port {self.port}"'"""
            subprocess.Popen(cmd, shell=True)
        elif system == "Linux":
            terminals = ["gnome-terminal", "xterm", "konsole"]
            for terminal in terminals:
                try:
                    subprocess.Popen(
                        [
                            terminal,
                            "--",
                            python_path,
                            client_path,
                            "--port",
                            str(self.port),
                        ]
                    )
                    break
                except FileNotFoundError:
                    continue
        else:
            raise RuntimeError("Unsupported operating system")

    def _setup_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("localhost", self.port))
        self.socket.listen(1)
        self.connection, _ = self.socket.accept()

    def get_input(self) -> Generator[Event, None, None]:
        message = self._send_request()

        yield from self.control_panel.extract_and_execute_commands(message)

    def _send_request(self):
        message_data = json.dumps(self.request)
        self.connection.send(message_data.encode())

        response = self.connection.recv(1024).decode()
        return response

    def cleanup(self):
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
