import json
import os
import platform
import socket
import subprocess
import sys
from collections.abc import Generator

from hermes.event import Event
from hermes.interface.assistant.chat_assistant.control_panel import (
    ChatAssistantControlPanel,
)
from hermes.interface.assistant.chat_assistant.interface import ChatAssistantInterface
from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.message import TextMessage


class DebugInterface(ChatAssistantInterface):
    def __init__(
        self,
        port=12345,
        control_panel: ChatAssistantControlPanel = None,
        model: ChatModel = None,
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

        yield from self.control_panel.break_down_and_execute_message(message)

    def _send_request(self):
        message_data = json.dumps(self.request)
        self.connection.send(message_data.encode())

        response = self.connection.recv(1024).decode()
        return TextMessage(author="assistant", text=response)

    def cleanup(self):
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
