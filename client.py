import socket
import threading
import os
import time
from protocol import BUFFER_SIZE, PACKAGE_TYPE_END, PACKAGE_TYPE_LS, PACKAGE_TYPE_PKG, PACKAGE_TYPE_REC, PACKAGE_TYPE_SYN, Protocol, Package

# def handle_client(socket, client_addr, request_packet, protocols):
#     with protocols_lock:
#         protocol = protocols.get(client_addr)
#         if protocol is None:
#             protocol = Protocol()
#             protocols[client_addr] = protocol
#         protocol.handle_request(socket, client_addr, request_packet)


def main():
    global server_socket
    server_socket = threading.Lock()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(('127.0.0.1', 9696))

    print(f"Server listening on {server_socket.getsockname()}")
    
    while True:
        print("Digite a ação que deseja fazer:")
        print("1 - Enviar arquivo")
        print("2 - Receber arquivo")
        print("3 - Listar arquivos")
        decisão = int(input())

        if decisão == 1:
            enviar_arquivo(server_socket)
        elif decisão == 2:
            receber_arquivo(server_socket)
        elif decisão == 3:
            listar_diretorio(server_socket)

def enviar_arquivo(server_socket):
    print("Digite o caminho para o arquivo:")
    filepath = input()
    if filepath == "":
        filepath = "./Equipe.txt"

    addr = input_addr()

    addr = addr.split(":")
    addr = tuple([addr[0], int(addr[1])])

    Protocol.handle_send_file_client(server_socket, addr, filepath)

def receber_arquivo(server_socket):
    data_list, addr = listar_diretorio(server_socket)

    print("Digite o número do arquivo que deseja receber:")
    file_number = int(input())

    filename = data_list[file_number]
    package = Package(addr, PACKAGE_TYPE_REC, 0, filename.encode())

    print("Enviado pedido de recebimento de arquivo para o servidor")

    protocol = Protocol()
    protocol.filename = filename.encode()
    #protocol.current_sequence = 1

    if Protocol.send_syn(server_socket, addr, f"a/{filename}"):
        server_socket.sendto(package.encode(), addr)
        while True:
            request_packet, client_addr = server_socket.recvfrom(BUFFER_SIZE*2)
            if protocol.handle_request(server_socket, addr, request_packet, True):
                break

def listar_diretorio(server_socket):
    addr = input_addr()
    addr = addr.split(":")
    addr = tuple([addr[0], int(addr[1])])

    package = Package(addr, PACKAGE_TYPE_LS)
    server_socket.sendto(package.encode(), addr)
    print("Enviado pedido de listagem de arquivos para o servidor")
    time.sleep(1)

    response, addr = server_socket.recvfrom(BUFFER_SIZE);
    response_packet = Package.decode(response)
    print("Arquivos disponíveis no servidor:\r\n")
    data = response_packet.data.decode('ISO-8859-15')
    data_list = data.replace("[", "").replace("]", "").replace('"', "").replace(' ', "").split(",")


    print(''.join(['-' for i in range(len(data))]))
    for i in range(len(data_list)):
        print(f"{i} - {data_list[i]}")
    print(''.join(['-' for i in range(len(data))]))

    return data_list, addr


def input_addr():
    print("Digite o endereço do cliente (IP:PORT):")
    addr = input()
    if addr == "":
        addr = "127.0.0.1:6969"

    return addr

if __name__ == "__main__":
    main()
