import socket
import threading
import re
#import rsa
#import fernet

HEADER = 512
FORMAT = "utf-8"
USERNAME = 256
PREFS = 256

# MSG that if found closes the connection to the client
DISCONNECT_MESSAGE = "!DISCONNECT"
REQ_LIST = "!REQ_LIST" + str(" " * (64 - len("!REQ_LIST")))

# Assuming host is on local machine
HOST = socket.gethostbyname(socket.gethostname())
PORT = 6463  # Specific port for Server-Client communication
NEW_PORT = 5050
ADDR = (HOST, PORT)
C_ADDR = (HOST, NEW_PORT)

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(C_ADDR)
listener.listen()

# STARTUP
print("Initiating connection to server...")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(ADDR)
except:
    print("ERROR (1): Could not connect to server. Please try again later.")
    exit(1)

print(f"Connected to server on {ADDR} \n")


def filter_illegal(input: str) -> str:
    input = input.replace("/n", "")
    input = input.replace(REQ_LIST, "")
    input = input.replace(DISCONNECT_MESSAGE, "")
    input = input.replace(" ", "")
    input = input.strip()
    return input


def send_to_server(msg: str, username: str, encryption: bool, discoverable: bool):
    """Send message to server in correct format

    Args:
        msg (string): Message to send in String
    """
    # HEADER
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    # Now pad to HEADER length
    send_length += b" " * (HEADER - len(send_length))
    client.send(send_length)

    # USERNAME
    username = username.encode(FORMAT)
    username_length = len(username)
    # Now pad to USERNAME length
    username += b" " * (USERNAME - (username_length))
    client.send(username)

    # TODO: Change client settings
    # Encryption=Y/N | Discoverable=Y/N |
    # Encryption: Asymmetric public-private key used to encrypt shared private RSA key,
    # which is then used to encrypt to data between clients.
    # encryption = True
    # discoverable = True
    prefs = (str(int(encryption)) + str(int(discoverable))).encode(FORMAT)
    prefs += b" " * (PREFS - len(prefs))
    client.send(prefs)

    client.send(message)
    # print("MESSAGE= '" + str(message) + "'")


def recv_msg_from_server() -> str:
    """Receive message from server"""
    msg_length = client.recv(HEADER).decode(FORMAT)
    if msg_length:  # If !msg_lenth.equals(null)
        msg_length = int(msg_length)

        msg = client.recv(msg_length).decode(FORMAT)
        # print("MSG NON EMPTY") #DEBUG
        return str(msg)


def recv_msg_peer(conn):
    # receive UDP message from another peer
    print("TODO")


def request_list_of_clients(username, encryption: bool, discoverable: bool):
    send_to_server(REQ_LIST, username, encryption, discoverable)
    clients_list = str(recv_msg_from_server())
    clients_list = clients_list.replace("|", "\n")
    clients_list = clients_list.rstrip("\n")
    return clients_list


def main():
    print("Enter your username: ")
    username = input(" > ")
    username_pre = username
    username = filter_illegal(username)
    if username_pre != username:
        print("Illegal characters found and removed. New username: '" + username + "'")

    print("\nDo you want to be discoverable to other clients? [Y/n]")
    discoverable = str(input(" > ")).lower()
    while (discoverable != "y") and (discoverable != "n"):
        print("Incorrect input: [Y/n]")
        discoverable = str(input(" > ".lower()))
    discoverable = True if discoverable == "y" else False

    print("\nDo you want an encrypted connection to other clients? [Y/n]")
    encrypted = str(input(" > ")).lower()
    while (encrypted != "y") and (encrypted != "n"):
        print("Incorrect input: [Y/n]")
        encrypted = str(input(" > ".lower()))
    encrypted = True if encrypted == "y" else False

    print("\nWaiting for clients...")
    clientList = request_list_of_clients(username, encrypted, discoverable)
    print(clientList)
    print("Select a client based on their ID (shown on the left):")
    peerID = input(" > ")
    peerID = int(peerID)
    peerAddr = re.split("\n", clientList)
    peerPrefs = re.split(":", peerAddr[peerID - 1])[3]
    peerUsername = re.split(":", peerAddr[peerID - 1])[1]
    peerAddr = re.split(":", peerAddr[peerID - 1])[2]
    
    split_string = peerAddr.strip('()').split(',')

    # Strip whitespace from each element and convert the second element to an integer
    result_tuple = (split_string[0].strip(), int(split_string[1].strip()))
    print("\nAttempting to connect to client " + peerUsername)
    initiate_chat(result_tuple)
    
    
    
    while 1:
        recv_msg_from_server()


def initiate_chat(target_addr):
    #Initiate a chat with another client
    chat_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chat_client.connect(target_addr)
    print("Chat initiated. Type your message:")
    while True:
        message = input()
        if message.lower() == "exit":
            chat_client.send(DISCONNECT_MESSAGE.encode(FORMAT))
            print("Chat ended.")
            break
        chat_client.send(message.encode(FORMAT))

def handle_incoming_connections():
    """Handle incoming connection requests from other clients"""
    while True:
        conn, addr = listener.accept()
        print(f"[INCOMING CONNECTION] {addr} connected.")
        threading.Thread(target=handle_incoming_messages, args=(conn, addr)).start()


def handle_incoming_messages(conn, addr):
    """Handle incoming messages from other clients"""
    while True:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            print(f"[{addr}] {msg}")
            if msg == DISCONNECT_MESSAGE:
                print(f"[DISCONNECTED] {addr} has disconnected.")
                conn.close()
                break


main()
# Need loop to be able to send and receive indefinitely
# Then it breaks out when a disconnect/close is requested

# send(DISCONNECT_MESSAGE)