from cctime import get_time
from network import Network, State
import socket
from ssl import create_default_context as create_ssl_context


class UnixNetwork(Network):
    def __init__(self, ssid, password, wifi_connect_delay=1):
        self.ssid = ssid
        self.password = password
        self.initialized = False
        self.initialize_delay = 1
        self.initialize_time = None
        self.wifi_connect_delay = wifi_connect_delay
        self.wifi_connect_time = None
        self.socket = None
        self.set_state(State.OFFLINE)

    def get_firmware_version(self):
        return 'None'

    def get_hardware_address(self):
        return '00:00:00:00:00:00'

    def set_state(self, new_state):
        self.state = new_state
        print(f'Network is now {self.state}.')

    def enable_step(self, ssid, password):
        if not self.initialized:
            if self.initialize_time:
                if get_time() > self.initialize_time:
                    self.initialized = True
                    self.initialize_time = None
            else:
                self.initialize_time = get_time() + self.initialize_delay

        elif self.state == State.OFFLINE:
            if self.wifi_connect_time:
                if get_time() > self.wifi_connect_time:
                    self.wifi_connect_time = None
                    self.set_state(State.ONLINE)
            elif ssid == self.ssid and password == self.password:
                self.wifi_connect_time = get_time() + self.wifi_connect_delay

    def connect_step(self, hostname, port=None, ssl=True):
        port = port or (443 if ssl else 80)
        print(f'Connecting to', hostname, 'port', port)
        sock = socket.create_connection((hostname, port))
        if ssl:
            context = create_ssl_context()
            sock = context.wrap_socket(sock, server_hostname=hostname)
        self.socket = sock
        self.set_state(State.CONNECTED)

    def send_step(self, data):
        if self.socket:
            self.socket.send(data)

    def receive_step(self, count):
        if self.socket:
            data = self.socket.recv(count)
            if len(data) == 0:
                self.close_step()
            return data

    def close_step(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.set_state(State.ONLINE)

    def disable_step(self):
        self.set_state(State.OFFLINE)
        self.initialized = False
