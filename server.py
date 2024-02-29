import socket
import threading

# get local ip address and set port to use
HOST = socket.gethostbyname(socket.gethostname())
PORT = 6463 # use specific port for TCP
ADDR = (HOST, PORT)

HEADER = 512
USERNAME = 2048
FORMAT = 'utf-8'

#MSG that if found closes the connection to the client
DISCONNECT_MESSAGE = "!DISCONNECT"
LISTENER_LIMIT = 15 #TODO: Set Limit if required
active_clients = [] # All currently connected users

def send_list_of_connections(conn, addr):
    """Send list of connections (that are discoverable) to a specific client

    Args:
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """
    
    user_list = ""
    for user in active_clients:
        user_list += "|".join([f"{user[0]}:{user[1]}:{user[2]}"])
    #user_list = "|".join([f"{user[0]}:{user[1]}" for user in active_clients])
    send_msgtoclient(user_list, conn, addr) 
    #print(user_list)

def handle_client(conn, addr):
    """Initiate and handle connection to a specific client

    Args:
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """
    
    # parallel client connection
    print(f"[New Connection] {addr} connected.")
    connected = True
    
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length: #If !msg_lenth.equals(null)
            msg_length = int(msg_length)
            
            #TODO: Read username for client
            username = conn.recv(USERNAME).decode(FORMAT).strip()
            if username:
                active_clients.append((username, addr, prefs)) 
            
            #TODO?
            #Change client settings
            
            #TODO?
            #
            
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
                print(f"[Closing Connection] {addr}")
            else:
                print(f"[{addr}] {msg}")
                
                #example server to client msg
                send_msgtoclient("THIS IS A TEST MESSAGE", conn, addr)
                send_list_of_connections(conn, addr)
            
    conn.close()

def send_msgtoclient(msg, conn, addr):
    """Send a message to a client through TCP, with the correct communication protocol

    Args:
        msg (string): Message in string format - unencrpyted
        conn (socket): Socket object of connection to client
        addr (_RetAddress): Return address part of socket object
    """
    
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    # pad to header length
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)

def main():
    
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
    
#call main
if __name__ == '__main__':
    main()