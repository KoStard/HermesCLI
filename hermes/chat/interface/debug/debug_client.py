import argparse
import json
import socket

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML


def parse_arguments():
    parser = argparse.ArgumentParser(description="Debug Interface Client")
    parser.add_argument("--port", type=int, default=12345, help="Port to connect to")
    return parser.parse_args()


def connect_to_server(port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to debug interface...")
    client_socket.connect(("localhost", port))
    print("Connected!")
    return client_socket


def main():
    args = parse_arguments()
    client_socket = connect_to_server(args.port)
    main_loop(client_socket)

def receive_buffer(client_socket):
    """Receive data from the socket with timeout handling."""
    buffer = []
    client_socket.settimeout(0.5)  # Set timeout for receiving data

    try:
        while True:
            chunk = client_socket.recv(4096).decode()
            if not chunk:
                break
            buffer.append(chunk)
    except TimeoutError:
        pass

    return "".join(buffer) if buffer else ""


def display_message_history(data):
    """Format and display the message history."""
    print("\nMessage History:")
    print("-" * 50)
    
    data = json.loads(data)
    try:
        for message in data["messages"]:
            print(message["role"])
            print(message["content"])
    except Exception:
        print(data)
    
    print("-" * 50)


def get_user_input():
    """Get input from the user using PromptSession."""
    session = PromptSession(
        history=None,
        auto_suggest=None,
        multiline=True,
        prompt_continuation=lambda width, line_number, is_soft_wrap: " " * width,
    )
    
    return session.prompt(HTML("\n<ansiyellow>Your response: </ansiyellow>"))


def process_communication_cycle(client_socket):
    """Process a single communication cycle with the server."""
    # Receive message history
    data = receive_buffer(client_socket)
    
    if not data:
        return
        
    # Display the message history
    display_message_history(data)
    
    # Get and send user input
    try:
        user_input = get_user_input()
        if user_input.strip():
            client_socket.send(user_input.encode())
    except KeyboardInterrupt:
        # Just return to main loop, which will continue
        pass

def main_loop(client_socket):
    """Main communication loop for the debug client."""
    try:
        while True:
            process_communication_cycle(client_socket)
    except KeyboardInterrupt:
        print("\nClosing debug client...")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
