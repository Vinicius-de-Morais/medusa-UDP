import socket
import threading
import time
from protocol import BUFFER_SIZE, Protocol, Package

def handle_client(socket, client_addr, request_packet, protocols):
    with protocols_lock:
        protocol = protocols.get(client_addr)
        if protocol is None:
            protocol = Protocol()
            protocols[client_addr] = protocol
        if protocol.handle_request(socket, client_addr, request_packet):
            del protocols[client_addr]

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 6969))
    print(f"Server listening on {server_socket.getsockname()}")

    global protocols_lock
    protocols_lock = threading.Lock()
    protocols = {}

    while True:
        time.sleep(0.1)
        request_packet, client_addr = server_socket.recvfrom(BUFFER_SIZE*2)
        threading.Thread(target=handle_client, args=(server_socket, client_addr, request_packet, protocols)).start()

if __name__ == "__main__":
    main()
