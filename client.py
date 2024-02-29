import socket

HEADER = 512
FORMAT = "utf-8"
USERNAME = 256
PREFS = 256

# MSG that if found closes the connection to the client
DISCONNECT_MESSAGE = "!DISCONNECT"

HOST = socket.gethostbyname(socket.gethostname())
PORT = 6463  # Specific port for Server-Client communication
ADDR = (HOST, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def send(msg):
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
    username = "BrafMeToo"
    username = "BrafMeToo".encode(FORMAT)
    username_length = len(username)
    # Now pad to USERNAME length
    username += b" " * (USERNAME - (username_length))
    client.send(username)

    # TODO: Change client settings
    # Encryption=Y/N | Discoverable=Y/N |
    # Encryption: Asymmetric public-private key used to encrypt shared private RSA key,
    # which is then used to encrypt to data between clients.
    encryption = False
    discoverable = True
    prefs = (str(int(encryption)) + str(int(discoverable))).encode(FORMAT)
    prefs += b" " * (PREFS - len(prefs))
    client.send(prefs)

    client.send(message)
    print("MESSAGE= '" + str(message) + "'")


def recv_msg():
    """Receive message from server"""
    msg_length = client.recv(HEADER).decode(FORMAT)
    if msg_length:  # If !msg_lenth.equals(null)
        msg_length = int(msg_length)

        #

        msg = client.recv(msg_length).decode(FORMAT)
        # print("MSG NON EMPTY") #DEBUG
        print(msg)


send("Hello World!")
while 1:
    recv_msg()

# Need loop to be able to send and receive indefinitely
# Then it breaks out when a disconnect/close is requested

# send(DISCONNECT_MESSAGE)
