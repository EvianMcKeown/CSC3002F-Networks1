import socket
import re
import threading
import rsa
from cryptography.fernet import Fernet
import sys, os

HEADER = 512
FORMAT = "utf-8"
USERNAME = 256
PREFS = 256
SHAREDKEY = 2048

# MSG that if found closes the connection to the client
DISCONNECT_MESSAGE = "!DISCONNECT"
REQ_LIST = "!REQUEST_LIST" + str(" " * (64 - len("!REQUEST_LIST")))

# Assuming host is on local machine
HOST = socket.gethostbyname(socket.gethostname())
PORT = 6463  # Specific port for Server-Client communication
ADDR = (HOST, PORT)

publicKey, privateKey = rsa.newkeys(512)
publicKey = publicKey.save_pkcs1(format="PEM") # Format able to send

sharedKey = Fernet.generate_key()
cipher = Fernet(sharedKey)

# STARTUP
print("Initiating connection to server...")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(ADDR)
except Exception:
    print("ERROR (1): Could not connect to server. Please try again later.")
    exit(1)

print(f"Connected to server on {ADDR} \n")


def splitAddrIntoIpPort(addr: str):
    addr = addr.split(",")
    addr_temp = str(addr[0]).replace("(", "").replace(")", "").replace(" ", "")
    addrPort = int(str(addr[1]).replace("(", "").replace(")", "").replace(" ", ""))
    addr = addr_temp
    return [addr, int(addrPort)]


def filter_illegal(input: str) -> str:
    temp = input
    temp = temp.replace("/n", "")
    temp = temp.replace(REQ_LIST, "")
    temp = temp.replace(DISCONNECT_MESSAGE, "")
    temp = temp.replace(" ", "")
    return temp.strip()


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
    return clients_list.rstrip("\n")


def find_lower_id_client(client_list, selfIP: str, selfPort, otherIP, otherPort):
    client_list = client_list.splitlines()
    # default to max 32-bit int
    selfID = sys.maxsize
    otherID = sys.maxsize

    for user in client_list:
        user = str(user).split(":")
        # print(user[2])
        # print(str(f"('{selfIP}', {selfPort})"))
        # print(str(user[2]) == str(f"('{selfIP}', {selfPort})"))
        if str(user[2]) == str(f"('{selfIP}', {selfPort})"):
            # found self
            selfID = user[0]
        if str(user[2]) == str(f"('{otherIP}', {otherPort})"):
            # found other client
            otherID = user[0]

    return selfPort if selfID <= otherID else otherPort


def initiate_chat(
    targetAddr, targetUsername, targetPrefs: str, ownPrefs: str, referencePort: int, ownUsername
):
    # Initiate a chat with another client
    targetAddr = str(targetAddr).split(",")
    targetAddr_temp = (
        str(targetAddr[0])
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "")
        .replace("'", "")
    )
    targetAddrPort = int(
        str(targetAddr[1]).replace("(", "").replace(")", "").replace(" ", "")
    )
    targetAddr = targetAddr_temp

    # socket for sending
    # source port: targetPort
    chat_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # chat_client.bind(("127.0.0.1", targetAddrPort - 1))

    # print("targetAddr =" + targetAddr)
    # print("targetAddrPort =" + str(targetAddrPort))
    # print("My local ip =" + str(HOST))

    # listen for incoming communication
    if int(referencePort) == int(targetAddrPort):
        # Case 1: other peer has reference port
        newReceivePort = int(referencePort) + 1
        newSendPort = int(referencePort) - 1
    else:
        # Case 2: we have reference port
        newReceivePort = int(referencePort) - 1
        newSendPort = int(referencePort) + 1

    # Determine if encrypted
    if (targetPrefs.strip()[0] == '1') or (ownPrefs.strip()[0] == '1') :
        encryption = True
    else:
        encryption = False
    
    threading.Thread(
        target=handle_incoming_connections,
        args=("127.0.0.1", newReceivePort, encryption, referencePort, targetAddrPort),
    ).start()
    print("Chat initiated. Type your message:")
    
    # Set necessary variables for connection loop (mostly default states)
    encryption = False
    connected = True
    ownPubKey = None
    ownPrivKey = None
    peerPubKey = None
    
    while connected:
        message = input(" > ").encode(FORMAT)
        msg_length = len(cipher.encrypt(message))
        send_length = str(msg_length).encode(FORMAT)
        # NOW PAD TO HEADER LENGTH
        send_length += b" " * (HEADER - len(send_length))
        chat_client.sendto(send_length, ("127.0.0.1", newSendPort))
        
        # USERNAME
        username = str(ownUsername).encode(FORMAT)
        username_length = len(username)
        # NOW PAD TO USERNAME LENGTH
        username += b" " * (USERNAME - len(send_length))
        chat_client.sendto(username, ("127.0.0.1", newSendPort))
        
        #PREFS: ENCRYPTION
        if (targetPrefs.strip()[0] == '1') or (ownPrefs.strip()[0] == '1') :
            # 2nd digit is T/F for encryption
            # Thus at least one client requires encryption
            encryption = True
            if (ownPubKey is None) or (ownPrivKey is None):
                # Create public and private asymmetric keys
                (ownPubKey, ownPrivKey) = (publicKey, privateKey)
                #print(ownPubKey, ownPrivKey)
                
                # One peer should create shared private key for actual data encryption
                # Assuming one that sends first creates it
                #sharedKey = Fernet.generate_key()
                #print(sharedKey)
                
                # create temp socket for key reception
                encryp_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if (str(targetAddrPort).strip() != str(referencePort).replace("'", "").strip()) :
                    # create temp socket for key reception
                    # Case 2: we have reference port
                    encryp_recvPort = int(referencePort) - 2
                    encryp_sendPort = int(referencePort) + 2
                    encrypt_recv_addr = ("127.0.0.1", encryp_recvPort)
                    encryp_recv.bind(encrypt_recv_addr)
                    
                else :
                    # case 1: peer has reference port
                    encryp_recvPort = int(referencePort) + 2
                    encryp_sendPort = int(referencePort) - 2
                    encrypt_recv_addr = ("127.0.0.1", encryp_recvPort)
                    encryp_recv.bind(encrypt_recv_addr)
                #    sharedKey = encryp_recv.recv(len())
                #cipher = Fernet(sharedKey)
                
                # TODO: receive peerPubKey, encrypt sharedKey with peerPubKey
                
                # send ownPubKey (size ? bits) through main socket
                chat_client.sendto(ownPubKey, ("127.0.0.1", newSendPort))
                # receive 512 bit key (64 bytes) through side
                peerPubKey = rsa.PublicKey.load_pkcs1(encryp_recv.recv(512), format='PEM')
            
            # Use peerPubKey to encrypt sharedKey
            encrypted_sharedKey = rsa.encrypt(sharedKey, peerPubKey)
            chat_client.sendto(encrypted_sharedKey, ("127.0.0.1", newSendPort))
            
            # TODO: encrypt msg with sharedkey
            if message.lower().decode(FORMAT) != "exit":
                # encrypt data with shared key
                encrypted_data = cipher.encrypt(message)
                chat_client.sendto(encrypted_data, ("127.0.0.1", newSendPort))
            else:
                encrypted_data = cipher.encrypt(DISCONNECT_MESSAGE.encode(FORMAT))
                chat_client.sendto(encrypted_data, ("127.0.0.1", newSendPort))
                print("Chat ended.")
                connected = False
                send_to_server(DISCONNECT_MESSAGE, username.decode(FORMAT), encryption, True)
                os._exit(0)
                break
        else:
            # no encryption
            if message.lower().decode(FORMAT) != "exit":
                chat_client.sendto(message, ("127.0.0.1", newSendPort))
            else:
                chat_client.sendto(DISCONNECT_MESSAGE.encode(FORMAT), ("127.0.0.1", newSendPort))
                print("Chat ended.")
                connected = False
                send_to_server(DISCONNECT_MESSAGE, username.decode(FORMAT), encryption, True)
                os._exit(0)
                break


def main():
    print("Enter your username: ")
    username = input(" > ")
    username_pre = username
    username = filter_illegal(username)
    if username_pre != username:
        print(f"Illegal characters found and removed. New username: '{username}'")

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

    # find lower ID client, to use port (with offset) for new port
    referencePort = find_lower_id_client(
        clientList,
        HOST,
        client.getsockname()[1],
        peerAddr.split(",")[0]
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .strip(),
        peerAddr.split(",")[1]
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .strip(),
    )
    # print(referencePort)

    initiate_chat(peerAddr, peerUsername, peerPrefs, ownPrefs, referencePort, username)

    while 1:
        recv_msg_from_server()


def handle_incoming_connections(serverAssignedIP, serverAssignedPort, encryption, referencePort, targetAddrPort):
    """Listen for incoming connections from other clients"""
    
    # Set variables for connection loop (mostly defaults)
    connected = True
    #encryption = False
    ownPubKey = None
    ownPrivKey = None
    peerPubKey = None
    sharedKey = None
    
    while connected:
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listeningAddr = (serverAssignedIP, serverAssignedPort)
        try:
            listener.bind(listeningAddr)
        except Exception:
            print("\n...Client is busy...\nPlease try again later.")
            os._exit(2)
            
        header = listener.recv(HEADER).decode(FORMAT)
        # Header received
        if header:
            # LENGTH OF MESSAGE AT END
            msg_length = int(str(header).strip())
            
            # GET USERNAME OF PEER
            username = listener.recv(USERNAME).decode(FORMAT)
            username = str(username).strip()
            
            # PREFS: ENCRYPTION
            if encryption :
                if (ownPubKey is None) or (ownPrivKey is None):
                    # create own pub-priv-key pair
                    (ownPubKey, ownPrivKey) = (publicKey, privateKey)
                    #sharedKey = Fernet.generate_key()
                    #cipher = Fernet(sharedKey)
                    
                    if (str(targetAddrPort).strip() == str(referencePort).replace("'", "").strip()) :
                        encryp_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        encryp_recvPort = int(referencePort) + 2
                        encryp_sendPort = int(referencePort) - 2
                        encryp_send_addr = ("127.0.0.1", encryp_sendPort)
                    else:
                        encryp_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        encryp_recvPort = int(referencePort) - 2
                        encryp_sendPort = int(referencePort) + 2
                        encryp_send_addr = ("127.0.0.1", encryp_sendPort)
                        
                    peerPubKey = rsa.PublicKey.load_pkcs1(listener.recv(512), format='PEM')
                    encryp_send.sendto(ownPubKey, ("127.0.0.1", encryp_sendPort))
                    
                # Receive encrypted sharedKey
                sharedKey = rsa.decrypt(listener.recv(64), ownPrivKey)
                cipher = Fernet(sharedKey)
                
                encrypted_msg = listener.recv(msg_length).decode(FORMAT)
                msg = cipher.decrypt(encrypted_msg).decode(FORMAT)
                
                if msg.lower().strip() == DISCONNECT_MESSAGE.lower():
                    print("Chat ended.")
                    connected = False
                    send_to_server(DISCONNECT_MESSAGE, username, encryption, True)
                    os._exit(0)
                print(f"{username}: {msg}")
            else :
                msg = listener.recv(msg_length).decode(FORMAT)
                if msg.lower().strip() == DISCONNECT_MESSAGE.lower():
                    print("Chat ended.")
                    connected = False
                    send_to_server(DISCONNECT_MESSAGE, username, encryption, True)
                    os._exit(0)
                print(f"{username}: {msg}")
        
        # print(header)


main()
# Need loop to be able to send and receive indefinitely
# Then it breaks out when a disconnect/close is requested

# send(DISCONNECT_MESSAGE)
