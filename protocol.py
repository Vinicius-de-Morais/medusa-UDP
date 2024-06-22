import socket

class Package:
    def _init_(self, address, package_type, sequence=0, data=None):
        self.address = address
        self.package_type = package_type
        self.sequence = sequence
        self.data = data if data else []

    @classmethod
    def from_bytes(cls, bytes_data, address):
        if len(bytes_data) < 4:
            return None
        package_type = bytes_data[:3].decode()
        sequence = bytes_data[3]
        data = bytes_data[4:]
        return cls(address, package_type, sequence, data)

    def to_bytes(self):
        return self.package_type.encode() + bytes([self.sequence]) + bytes(self.data)

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

    def new_data(self, sequence, data):
        self.package_type = 'PKG'
        self.sequence = sequence
        self.data = data
        return self


class Protocol:
    def _init_(self):
        self.packages = []
        self.current_sequence = 0
        self.current_ack = 0
        self.current_nak = 0
        self.resolved = False

    def handle_request(self, socket, client_addr, request_packet):
        request_packet = Package.from_bytes(request_packet, client_addr)
        if request_packet.package_type == 'SYN':
            self.handle_syn(socket, client_addr)
        elif request_packet.package_type == 'PKG':
            self.handle_pkg(request_packet, socket, client_addr)
        elif request_packet.package_type == 'END':
            self.handle_end(socket, client_addr)
        else:
            self.send_nak(socket, client_addr)

    def handle_syn(self, socket, client_addr):
        self.send_ack(socket, client_addr)

    def send_ack(self, socket, client_addr):
        self.current_ack += 1
        response_packet = Package.new(client_addr).ack().to_bytes()
        socket.sendto(response_packet, client_addr)

    def send_nak(self, socket, client_addr):
        self.current_nak += 1
        response_packet = Package.new(client_addr).nak().to_bytes()
        socket.sendto(response_packet, client_addr)

    def handle_pkg(self, request_packet, socket, client_addr):
        if request_packet.sequence == self.current_sequence:
            self.add_package(request_packet)
            self.send_ack(socket, client_addr)
        else:
            self.send_nak(socket, client_addr)

    def add_package(self, package):
        self.packages.append(package)
        self.current_sequence += 1

    def handle_end(self, socket, client_addr):
        self.resolved = True
        self.packages.sort(key=lambda p: p.sequence)
        path = f"{client_addr}_file.txt"
        with open(path, 'wb') as file:
            for package in self.packages:
                file.write(package.data)
        self.send_ack(socket, client_addr)
        self.packages.clear()

    def send_file(self, socket, client_addr):
        for package in self.packages:
            socket.sendto(package.to_bytes(), client_addr)

# Define package types as constants
PACKAGE_TYPE_SYN = 'SYN'
PACKAGE_TYPE_ACK = 'ACK'
PACKAGE_TYPE_NAK = 'NAK'
PACKAGE_TYPE_PKG = 'PKG'
PACKAGE_TYPE_END = 'END'import socket

class Package:
    def _init_(self, address, package_type, sequence=0, data=None):
        self.address = address
        self.package_type = package_type
        self.sequence = sequence
        self.data = data if data else []

    @classmethod
    def from_bytes(cls, bytes_data, address):
        if len(bytes_data) < 4:
            return None
        package_type = bytes_data[:3].decode()
        sequence = bytes_data[3]
        data = bytes_data[4:]
        return cls(address, package_type, sequence, data)

    def to_bytes(self):
        return self.package_type.encode() + bytes([self.sequence]) + bytes(self.data)

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

    def new_data(self, sequence, data):
        self.package_type = 'PKG'
        self.sequence = sequence
        self.data = data
        return self


class Protocol:
    def _init_(self):
        self.packages = []
        self.current_sequence = 0
        self.current_ack = 0
        self.current_nak = 0
        self.resolved = False

    def handle_request(self, socket, client_addr, request_packet):
        request_packet = Package.from_bytes(request_packet, client_addr)
        if request_packet.package_type == 'SYN':
            self.handle_syn(socket, client_addr)
        elif request_packet.package_type == 'PKG':
            self.handle_pkg(request_packet, socket, client_addr)
        elif request_packet.package_type == 'END':
            self.handle_end(socket, client_addr)
        else:
            self.send_nak(socket, client_addr)

    def handle_syn(self, socket, client_addr):
        self.send_ack(socket, client_addr)

    def send_ack(self, socket, client_addr):
        self.current_ack += 1
        response_packet = Package.new(client_addr).ack().to_bytes()
        socket.sendto(response_packet, client_addr)

    def send_nak(self, socket, client_addr):
        self.current_nak += 1
        response_packet = Package.new(client_addr).nak().to_bytes()
        socket.sendto(response_packet, client_addr)

    def handle_pkg(self, request_packet, socket, client_addr):
        if request_packet.sequence == self.current_sequence:
            self.add_package(request_packet)
            self.send_ack(socket, client_addr)
        else:
            self.send_nak(socket, client_addr)

    def add_package(self, package):
        self.packages.append(package)
        self.current_sequence += 1

    def handle_end(self, socket, client_addr):
        self.resolved = True
        self.packages.sort(key=lambda p: p.sequence)
        path = f"{client_addr}_file.txt"
        with open(path, 'wb') as file:
            for package in self.packages:
                file.write(package.data)
        self.send_ack(socket, client_addr)
        self.packages.clear()

    def send_file(self, socket, client_addr):
        for package in self.packages:
            socket.sendto(package.to_bytes(), client_addr)

# Define package types as constants
PACKAGE_TYPE_SYN = 'SYN'
PACKAGE_TYPE_ACK = 'ACK'
PACKAGE_TYPE_NAK = 'NAK'
PACKAGE_TYPE_PKG = 'PKG'
PACKAGE_TYPE_END = 'END'
