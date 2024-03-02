import socket
import threading
import re

# import rsa
# import fernet

# get local ip address and set port to use
HOST = socket.gethostbyname(socket.gethostname())
PORT = 6463  # use specific port for TCP
ADDR = (HOST, PORT)
SERVER_USERNAME = "server"

HEADER = 512
USERNAME = 256
PREFS = 256
FORMAT = "utf-8"

# MSG that if found closes the connection to the client
DISCONNECT_MESSAGE = "!DISCONNECT"
REQ_LIST = "!REQ_LIST" + str(" " * (64 - len("!REQ_LIST")))
LISTENER_LIMIT = 15  # TODO: Set Limit if required
active_clients = []  # All currently connected users


def send_list_of_connections(conn, addr):
    """Send list of connections (that are discoverable) to a specific client

    Args:
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """

    user_list = ""
    usercount = 0
    for user in active_clients:
        # If second char in prefs string = 1, then client is discoverable
        if re.match(".1", user[2]):
            usercount += 1
            user_list += f"{usercount}:{user[0]}:{user[1]}:{user[2]}|"
    # user_list = "|".join([f"{user[0]}:{user[1]}" for user in active_clients])
    send_msgtoclient(user_list, conn, addr)
    # print(user_list)


def handle_client(conn, addr):
    """Initiate and handle connection to a specific client

    Args:
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """

    # parallel client connection
    print(f"[New Connection] {addr} connected.")
    connected = True
    encryption = False
    server_pubkey = None
    server_privkey = None
    client_pubkey = None

    loopCount = 0
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:  # If !msg_lenth.equals(null)
            msg_length = int(msg_length)

            # Read username for client
            username = conn.recv(USERNAME).decode(FORMAT).strip()

            # Encryption=Y/N | Discoverable=Y/N |
            # Encryption: Asymmetric public-private key used to encrypt shared private RSA key,
            # which is then used to encrypt to data between clients.
            prefs = conn.recv(PREFS).decode(FORMAT).strip()
            # print("PREFS= '" + prefs + "'")

            if username:
                active_clients.append((username, addr, prefs))

            # TODO?
            # Change client settings
            # if re.match("1.", prefs):
            # Encryption
            # encryption = True
            # if (server_pubkey is None) or (server_privkey is None):
            # Create public and provate asymmetric keys
            # (server_pubkey, server_privkey) = rsa.newkeys(2048)
            # Create shared provate key for actual data encryption
            # shared_key = fernet.generate_key()
            # cipher = fernet(shared_key)
            # encrypt data with shared key
            # encrypted_data = cipher.encrypt("some data")
            # encrypt shared key with public key
            # encrypted_shared_key = rsa.encrypt(shared_key, server_pubkey)

            # crypto = rsa.encrypt(messa)

            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
                print(f"[Closing Connection] {addr}")
            elif msg == REQ_LIST:
                send_list_of_connections(conn, addr)
            else:
                print(f"[{addr}] {msg}")

                # example server to client msg
                # send_msgtoclient("THIS IS A TEST MESSAGE", conn, addr)
                # send_list_of_connections(conn, addr)

    conn.close()


def send_msgtoclient(msg, conn, addr):
    """Send a message to a client through TCP, with the correct communication protocol

    Args:
        msg (string): Message in string format - unencrpyted
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """

    message = msg.encode(FORMAT)
    # HEADER
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    # pad to header length
    send_length += b" " * (HEADER - len(send_length))
    conn.send(send_length)
    # END HEADER

    conn.send(message)


def main():
    """main method"""

    # TCP uses SOCK_STREAM
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # UDP uses SOCK_DGRAM
    # server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(ADDR)

    print("Starting server...")
    server.listen(LISTENER_LIMIT)
    print(f"Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr)).start()

        print(f"[No. of Active Connections] {threading.active_count() - 1}")


# call main method
if __name__ == "__main__":
    main()
