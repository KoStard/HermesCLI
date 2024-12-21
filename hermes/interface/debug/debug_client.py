import socket
import argparse
import json

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
            
                # Get user input
                user_input = input("\nYour response: ")
                
                # Send response back to server
                client_socket.send(user_input.encode())

            # client_socket.settimeout(None)  # Reset timeout for next iteration

    except KeyboardInterrupt:
        print("\nClosing debug client...")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()

