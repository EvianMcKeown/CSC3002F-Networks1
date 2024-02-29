import socket
import threading

HOST = '127.0.0.1'
PORT = 1234
FORMAT = 'utf-8'

def listen_for_messages_from_server(client):
    while 1:
        message = client.recv(2048).decode(FORMAT)
        if message != '':
            username = message.split("~")[0]
            content = message.split("~")[1]
            print(f"[{username}] {content}")
        else:
            print("Message received from client is empty.")

def send_message_to_server(client):
    while 1:
        message = input("Message: ")
        if message != '':
            client.sendall(message.encode())
        else:
            print("Empty message.")
            exit(0)


def server_communication(client):
    username = input("Enter username:")

    if username != '':
        client.sendall(username.encode())
    else:
        print("Username cannot be empty.")
        exit(0)

    threading.Thread(target=listen_for_messages_from_server, args=(client,)).start()
    send_message_to_server(client)

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        print("Successfully connected to server.")
    except:
        print(f"Unable to connect to server {HOST} {PORT}")

    server_communication(client)

if __name__ == '__main__':
    main()