import socket
import threading
import os
import time
from protocol import BUFFER_SIZE, PACKAGE_TYPE_END, PACKAGE_TYPE_LS, PACKAGE_TYPE_PKG, PACKAGE_TYPE_SYN, Protocol, Package

# def handle_client(socket, client_addr, request_packet, protocols):
#     with protocols_lock:
#         protocol = protocols.get(client_addr)
#         if protocol is None:
#             protocol = Protocol()
#             protocols[client_addr] = protocol
#         protocol.handle_request(socket, client_addr, request_packet)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', 9696))

    print(f"Server listening on {server_socket.getsockname()}")

    print("Digite a ação que deseja fazer:")
    print("1 - Enviar arquivo")
    print("2 - Receber arquivo")
    print("3 - Listar arquivos")
    decisão = int(input())

    if decisão == 1:
        enviar_arquivo(server_socket)
    elif decisão == 2:
        print("n implementado ainda")
        #receber_arquivo(server_socket)
    elif decisão == 3:
        print("n implementado ainda")
        listar_diretorio(server_socket)

def enviar_arquivo(server_socket):
    print("Digite o caminho para o arquivo:")
    filepath = input()
    if filepath == "":
        filepath = "./Equipe.txt"

    addr = input_addr()

    addr = addr.split(":")
    addr = tuple([addr[0], int(addr[1])])

    Protocol.handle_send_file(server_socket, addr, filepath)
 
def listar_diretorio(server_socket):
    addr = input_addr()
    addr = addr.split(":")
    addr = tuple([addr[0], int(addr[1])])

    package = Package(addr, PACKAGE_TYPE_LS)
    server_socket.sendto(package.encode(), addr)
    print("Enviado pedido de listagem de arquivos para o servidor")
    time.sleep(0.01)

    response, addr = server_socket.recvfrom(BUFFER_SIZE);
    response_packet = Package.decode(response)
    print("Arquivos disponíveis no servidor:\r\n")
    data = response_packet.data.decode('ISO-8859-15')
    print(data)
    print(''.join(['-' for i in range(len(data))]))

def input_addr():
    print("Digite o endereço do cliente (IP:PORT):")
    addr = input()
    if addr == "":
        addr = "127.0.0.1:6969"

    return addr

if __name__ == "__main__":
    main()
