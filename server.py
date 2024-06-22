import socket
import threading
from protocol import Protocol, Package

def handle_client(socket, client_addr, request_packet, protocols):
    with protocols_lock:
        protocol = protocols.get(client_addr)
        if protocol is None:
            protocol = Protocol()
            protocols[client_addr] = protocol
        protocol.handle_request(socket, client_addr, request_packet)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', 6969))
    print(f"Server listening on {server_socket.getsockname()}")

    global protocols_lock
    protocols_lock = threading.Lock()
    protocols = {}

    while True:
        request_packet, client_addr = server_socket.recvfrom(1024)
        threading.Thread(target=handle_client, args=(server_socket, client_addr, request_packet, protocols)).start()

if _name_ == "_main_":
    main()