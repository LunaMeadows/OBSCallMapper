"""
Server side of the obs plugin. Used to send information to obs
"""
import socket

class Server:
    """
        OBSPluginServer is the server host for the obs plugin to map cameras inside obs.
        It connects to obs and then sends commands to the plugin with camera positions, names, and other info needed.

        Attributes
        ----------
        host : int
            host ip address
        port : int
            port for server communication
        """
    def __init__(self, port=48387):
        """
        Sets up global variables for server

        :param port: port for sever communication
        """
        self.port = port
        self.server_socket = None

    def start_server(self):
        """
        Starts server for the obs plugin
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_command(self, msg):
        """
        Sends command to obs plugin client
        :param msg: command message
        """
        self.server_socket.sendto(bytes(str(msg), "utf-8"), ('localhost', self.port))
