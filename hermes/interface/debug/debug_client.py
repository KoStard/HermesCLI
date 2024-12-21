import socket
import argparse
import json
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

def main():
    parser = argparse.ArgumentParser(description='Debug Interface Client')
    parser.add_argument('--port', type=int, default=12345, help='Port to connect to')
    args = parser.parse_args()

    # Connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to debug interface...")
    client_socket.connect(('localhost', args.port))
    print("Connected!")

    try:
        while True:
            # Receive message history from server with buffering
            buffer = []
            client_socket.settimeout(0.5)  # Set timeout for receiving data
            
            try:
                while True:
                    chunk = client_socket.recv(4096).decode()
                    if not chunk:
                        break
                    buffer.append(chunk)
            except socket.timeout:
                if not buffer:
                    continue

            if buffer:
                data = ''.join(buffer)
                # Display the message history
                print("\nMessage History:")
                print("-" * 50)
                data = json.loads(data)
                try:
                    for message in data['messages']:
                        print(message['role'])
                        print(message['content'])
                except Exception:
                    print(data)
                print("-" * 50)
            
                session = PromptSession(
                    history=None,
                    auto_suggest=None,
                    multiline=True,
                    prompt_continuation=lambda width, line_number, is_soft_wrap: ' ' * width,
                )

                # Get user input
                try:
                    user_input = session.prompt(HTML("\n<ansiyellow>Your response: </ansiyellow>"))
                    if user_input.strip():
                        # Send response back to server
                        client_socket.send(user_input.encode())
                except KeyboardInterrupt:
                    continue

            # client_socket.settimeout(None)  # Reset timeout for next iteration

    except KeyboardInterrupt:
        print("\nClosing debug client...")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()

