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
            # Receive message history from server
            data = client_socket.recv(4096).decode()
            if not data:
                break

            # Display the message history
            print("\nMessage History:")
            print("-" * 50)
            print(data)
            print("-" * 50)

            # Get user input
            user_input = input("\nYour response: ")
            
            # Send response back to server
            client_socket.send(user_input.encode())

    except KeyboardInterrupt:
        print("\nClosing debug client...")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()

