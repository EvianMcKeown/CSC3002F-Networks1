import socket
import threading

HOST = '127.0.0.1'
PORT = 1234
LISTENER_LIMIT = 15
FORMAT = 'utf-8'
active_clients = [] # All currently connected users 

# Function to listen for client connections
def listen_for_messages(client, username):
    while 1:
        message = client.recv(2048).decode(FORMAT)
        if message != '':
            final_message = username + '~' + message
            send_messages_to_all(final_message)
        else:
            print(f"The message sent from user {username} is empty.")

# Function to send messages to all the clients currently connected to the server
def send_messages_to_all(message):
    for user in active_clients:
        send_message_to_client(user[1], message)

# Function to send messages to one specific client
def send_message_to_client(client, message):
    client.sendall(message.encode())

def client_handler(client):
    # server listens for username
    while 1:
        username = client.recv(2048).decode(FORMAT)
        if username != '':
            active_clients.append((username, client))
            break
        else:
            print("Client username is empty")

    threading.Thread(target=listen_for_messages, args=(client, username,)).start()

# Main method where the server and client are bound
def main():
    # We are using UDP packets for communication. 
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((HOST, PORT))
        print(f"Running the server on {HOST} {PORT}")
    except:
        print(f"Unable to bind to host {HOST} and port {PORT}")

    # Set server limit
    server.listen(LISTENER_LIMIT)

    # While loop to listen for client connections
    while 1:
        client, address = server.accept()
        print(f"Successfully connected to client {address[0]} {address[1]}")

        threading.Thread(target=client_handler, args=(client, )).start()

if __name__ == '__main__':
    main()