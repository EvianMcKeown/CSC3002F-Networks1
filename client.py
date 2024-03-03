import socket
import re
import threading
import rsa
import fernet

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
ADDR = (HOST, PORT)

# STARTUP
print("Initiating connection to server...")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(ADDR)
except:
    print("ERROR (1): Could not connect to server. Please try again later.")
    exit(1)

print(f"Connected to server on {ADDR} \n")


def splitAddrIntoIpPort(addr: str):
    addr = str(addr).split(",")
    addr_temp = str(addr[0]).replace("(", "").replace(")", "").replace(" ", "")
    addrPort = int(str(addr[1]).replace("(", "").replace(")", "").replace(" ", ""))
    addr = addr_temp
    return [addr, int(addrPort)]


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


def initiate_chat(targetAddr, targetUsername, targetPrefs, ownPrefs):
    # Initiate a chat with another client
    targetAddr = str(targetAddr).split(",")
    targetAddr_temp = (
        str(targetAddr[0]).replace("(", "").replace(")", "").replace(" ", "").replace("'", "")
    )
    targetAddrPort = int(
        str(targetAddr[1]).replace("(", "").replace(")", "").replace(" ", "")
    )
    targetAddr = targetAddr_temp

    #socket for sending
    #source port: targetPort 
    chat_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chat_client.bind(("127.0.0.1", targetAddrPort - 1))

    print("targetAddr =" + targetAddr)
    print("targetAddrPort =" + str(targetAddrPort))
    print("My local ip =" + str(HOST))
    
    #listen for incoming communication
    threading.Thread(
        target=handle_incoming_connections,
        args=(targetAddr, 10000),
    ).start()
    print("Chat initiated. Type your message:")
    while True:
        message = input(" > ")
        if message.lower() == "exit":
            chat_client.send(DISCONNECT_MESSAGE.encode(FORMAT))
            print("Chat ended.")
            break
        chat_client.sendto(message.encode(FORMAT), (targetAddr, 10001))


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

    ownPrefs = str(int(encrypted)) + str(int(discoverable))

    print("\nWaiting for clients...")
    clientList = request_list_of_clients(username, encrypted, discoverable)
    print(clientList)
    print("Select a client based on their ID (shown on the left):")
    # TODO error checking
    peerID = int(input(" > "))
    peerAddr = re.split("\n", clientList)
    peerPrefs = re.split(":", peerAddr[peerID - 1])[3]
    peerUsername = re.split(":", peerAddr[peerID - 1])[1]
    peerAddr = re.split(":", peerAddr[peerID - 1])[2]

    print("\nAttempting to connect to client " + peerUsername)

    initiate_chat(peerAddr, peerUsername, peerPrefs, ownPrefs)

    while 1:
        recv_msg_from_server()


def handle_incoming_connections(serverAssignedIP, serverAssignedPort):
    """Listen for incoming connections from other clients"""
    while 1:
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listeningAddr = (serverAssignedIP, serverAssignedPort)
        listener.bind(listeningAddr)
        header = listener.recv(HEADER).decode(FORMAT)
        print(header)


main()
# Need loop to be able to send and receive indefinitely
# Then it breaks out when a disconnect/close is requested

# send(DISCONNECT_MESSAGE)
