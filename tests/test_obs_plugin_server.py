import pytest
from mappingUtils import obs_plugin_server

def test_start_server():
    server = obs_plugin_server.Server()
    assert server.start_server() is None

def test_send_command():
    server = obs_plugin_server.Server()
    server.start_server()
    assert server.send_command('Hello') is None