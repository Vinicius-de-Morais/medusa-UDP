import json
import os
import socket
from pathlib import Path
import time

class Package:
    def __init__(self, address, package_type, sequence=0, data=None):
        self.address = address
        self.package_type = package_type
        self.sequence = sequence
        self.data = data if data else b''

    def to_dict(self) -> dict:
        """Converts the Package object to a dictionary."""

        print(f"\r\nPackage to dict: {self.data}\r\n\r\n")

        return {
            'address': self.address,
            'package_type': self.package_type,
            'sequence': self.sequence,
            'data': self.data.decode('ISO-8859-15')  # Convert bytes to string for JSON serialization
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a Package object from a dictionary."""
        return cls(
            address=tuple(data['address']),
            package_type=data['package_type'],
            sequence=data['sequence'],
            data=data['data'].encode('ISO-8859-15')  # Convert string back to bytes
        )

    def encode(self) -> bytes:
        """Encodes the Package object into a JSON byte stream."""
        return json.dumps(self.to_dict()).encode('ISO-8859-15')

    @classmethod
    def decode(cls, byte_data: bytes):
        """Decodes the JSON byte stream back into a Package object."""
        return cls.from_dict(json.loads(byte_data.decode('ISO-8859-15')))

    @staticmethod
    def new(address):
        return Package(address, 'SYN')

    def syn(self):
        self.package_type = 'SYN'
        return self

    def ack(self):
        self.package_type = 'ACK'
        return self

    def nak(self):
        self.package_type = 'NAK'
        return self
    
    def end(self):
        self.package_type = 'END'
        return self

    def new_data(self, sequence, data):
        self.package_type = 'PKG'
        self.sequence = sequence
        self.data = data
        return self

    def __repr__(self):
        return f"Package(address={self.address}, package_type={self.package_type}, sequence={self.sequence}, data={self.data})"

class Protocol:
    def __init__(self):
        self.packages = []
        self.current_sequence = 0
        self.current_ack = 0
        self.current_nak = 0
        self.resolved = False
        self.filename = None

    def handle_request(self, socket, client_addr, request_packet, from_client = False):

        print(f"Received \n\r {request_packet}\n\r from {client_addr}\n\r")

        request_packet = Package.decode(request_packet)

        if request_packet.package_type == 'SYN':
            self.handle_syn(socket, client_addr, request_packet)
        elif request_packet.package_type == 'PKG':
            self.handle_pkg(request_packet, socket, client_addr)
        elif request_packet.package_type == 'END':
            self.handle_end(socket, client_addr, f"{client_addr[0]}_file/")
            if from_client:
                return True

        elif request_packet.package_type == 'LS':
            Protocol.handle_ls(socket, client_addr)
        elif request_packet.package_type == 'REC':
            self.send_file_to_Client(socket, client_addr, request_packet)
        elif request_packet.package_type == 'ACK':
            sequence = self.hadle_send_response(request_packet.encode(), client_addr)
            if sequence != -1:
                self.send_file(socket, client_addr, request_packet.sequence)
        
        # else:
        #     self.send_nak(socket, client_addr)

    def handle_syn(self, socket, client_addr, request_packet):
        self.filename = request_packet.data
        self.current_sequence += 1
        self.packages.clear()
        self.send_ack(socket, client_addr)

    def send_ack(self, socket, client_addr):
        self.current_ack += 1
        response_packet = Package(client_addr, 'ACK', self.current_sequence).encode()
        socket.sendto(response_packet, client_addr)

    def send_nak(self, socket, client_addr):
        self.current_nak += 1
        print(f"NAK sent to {client_addr}\n Current sequence: {self.current_sequence}\n Current NAK: {self.current_nak}\n\r")
        #self.current_sequence -= self.current_nak
        
        response_packet = Package(client_addr, 'NAK', self.current_sequence).encode()
        socket.sendto(response_packet, client_addr)

    def send_end(self, socket, client_addr):
        response_packet = Package.new(client_addr).end().encode()
        socket.sendto(response_packet, client_addr)

    def handle_pkg(self, request_packet, socket, client_addr):
        #if request_packet.sequence == self.current_sequence:
            self.add_package(request_packet)
            if self.current_sequence % 3 == 0:
                self.send_ack(socket, client_addr)
        #else:
        #    self.send_nak(socket, client_addr)

    def add_package(self, package):
        self.packages.append(package)
        self.current_sequence += 1

    def handle_end(self, socket, client_addr: tuple, path):
        self.resolved = True
        self.packages.sort(key=lambda p: p.sequence)

        Path(path).mkdir(parents=True, exist_ok=True)
        with open(path+self.filename.decode(), 'ab') as file:
            for package in self.packages:
                if package.package_type == 'PKG':
                    file.write(package.data)
        self.send_end(socket, client_addr)
        self.packages.clear()

    def handle_ls(socket, client_addr):
        files = os.listdir(f"{client_addr[0]}_file/")
        response = Package(client_addr, PACKAGE_TYPE_LS, 0, json.dumps(files).encode())
        socket.sendto(response.encode(), client_addr)

    def send_file_to_Client(self, socket, client_addr, request_packet):
        file_name = request_packet.data.decode('ISO-8859-15')

        file_path = f"{client_addr[0]}_file/{file_name}"
        self.handle_send_file(socket, client_addr, file_path)

    ##
    ## coisas para enviar arquivo
    ##


    def send_file_client(self, socket, client_addr):
        sequence = 0
        self.packages.sort(key=lambda p: p.sequence)

        while True:
            if len(self.packages) > sequence:
                for _ in range(3):
                    package: Package = self.packages[sequence]
                    sequence += 1
                    try:
                        package_bytes = package.encode()
                        socket.sendto(package_bytes, client_addr)
                        time.sleep(0.01)

                        if len(self.packages) == sequence:
                            break
                    except socket.timeout:
                        pass
            
            response_bytes, _ = socket.recvfrom(BUFFER_SIZE)
            sequence = self.hadle_send_response(response_bytes, client_addr)
            if sequence == -1:
                break
    
    # metodo para o servidor
    def send_file(self, socket, client_addr, sequence = 0):
        self.packages.sort(key=lambda p: p.sequence)

        while True:
            if len(self.packages) > sequence:
                for _ in range(3):
                    package: Package = self.packages[sequence]
                    sequence += 1
                    try:
                        package_bytes = package.encode()
                        socket.sendto(package_bytes, client_addr)
                        time.sleep(0.01)

                        if len(self.packages) == sequence:
                            break
                    except socket.timeout:
                        pass

    @classmethod
    def hadle_send_response(self, response_bytes, client_addr):
        #response = Package.from_bytes(response_bytes, client_addr)
        response = Package.decode(response_bytes)
        if response != None:
            if response.package_type == PACKAGE_TYPE_ACK:
                return response.sequence
            elif response.package_type == PACKAGE_TYPE_NAK:
                return response.sequence
            elif response.package_type == PACKAGE_TYPE_END:
                return -1
        else:
            return -1

    @staticmethod
    def handle_send_file_client(socket, addr, filepath):
        # EM MEDIA OS OUTROS ELEMENTOS OCUPAM 75 BYTES SEM OS DADOS, ENTAO SUBTRAINDO 75 DO BUFFER_SIZE
        # {"address": ["127.0.0.1", 6969], "package_type": "PKG", "sequence": 1, ...
        buffer = BUFFER_SIZE //5 # - 75

        packet_count = Protocol.get_file_packet_count(filepath, buffer)
        filesize = os.path.getsize(filepath)

        print(f"Tamanho do arquivo {filesize}")
        print(f"serão enviados {packet_count} pacotes")

        protocol = Protocol.fill_packages_client(filepath, buffer, addr)

        if Protocol.send_syn(socket, addr, filepath):
            Protocol.send_package_client(socket, addr, protocol)

    # metodo para servidor
    def handle_send_file(self, socket, addr, filepath):
        # EM MEDIA OS OUTROS ELEMENTOS OCUPAM 75 BYTES SEM OS DADOS, ENTAO SUBTRAINDO 75 DO BUFFER_SIZE
        # {"address": ["127.0.0.1", 6969], "package_type": "PKG", "sequence": 1, ...
        buffer = BUFFER_SIZE //5 # - 75

        packet_count = Protocol.get_file_packet_count(filepath, buffer)
        filesize = os.path.getsize(filepath)

        print(f"Tamanho do arquivo {filesize}")
        print(f"serão enviados {packet_count} pacotes")

        self.fill_packages(filepath, buffer, addr)
        self.send_package(socket, addr)

    def get_file_packet_count(filename, buffer_size):
        byte_size = os.stat(filename).st_size
        
        packet_count = byte_size//buffer_size

        if byte_size%buffer_size:
            packet_count += 1

        return packet_count

    def data_to_pkg(addr, data, seq_number):
        return Package(addr, PACKAGE_TYPE_PKG, seq_number, data)

    # Preenche o protocolo com os pacotes do arquivo
    def fill_packages_client(filename, buffer_size, addr):
        protocol = Protocol()

        with open(filename, 'rb') as file:
            data = file.read(buffer_size)
            seq_number = 0

            while data:
                seq_number += 1
                protocol.add_package(Protocol.data_to_pkg(addr, data, seq_number))
                data = file.read(buffer_size)

        protocol.add_package(Package(addr, PACKAGE_TYPE_END, seq_number+1, None))
        return protocol

    # metodo para o servidor
    def fill_packages(self, filename, buffer_size, addr):
        with open(filename, 'rb') as file:
            data = file.read(buffer_size)
            seq_number = 0

            while data:
                seq_number += 1
                self.add_package(Protocol.data_to_pkg(addr, data, seq_number))
                data = file.read(buffer_size)

        self.add_package(Package(addr, PACKAGE_TYPE_END, seq_number+1, None))

    def send_syn(socket, client_addr, path) -> bool:
        
        filename = path.split("/")[-1]
        syn = Package(client_addr, PACKAGE_TYPE_SYN, 0, filename.encode())
        socket.sendto(syn.encode(), client_addr)

        data, addr = socket.recvfrom(BUFFER_SIZE)
        response = Package.decode(data)
        if response.package_type == "ACK":
            print(f"\nACK received from {client_addr}\n")
            return True
        else:
            print(f"\nNAK received from {client_addr}\n")
            return False

    def send_package_client(socket, client_addr, protocol):
        protocol.send_file_client(socket, client_addr)

    def send_package(self, socket, client_addr):
        self.send_file(socket, client_addr)


# Define package types as constants
PACKAGE_TYPE_SYN = 'SYN'
PACKAGE_TYPE_ACK = 'ACK'
PACKAGE_TYPE_NAK = 'NAK'
PACKAGE_TYPE_PKG = 'PKG'
PACKAGE_TYPE_END = 'END'
PACKAGE_TYPE_LS = 'LS'
PACKAGE_TYPE_REC = 'REC'

BUFFER_SIZE = 1024