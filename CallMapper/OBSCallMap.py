import obspython as obs
import socket
import threading

server = None
server_run = True

# ------------------------------------------------------------

def crop_cam():
    source=obs.obs_get_source_by_name("Window Capture")
    crop = obs.obs_source_get_filter_by_name(source, "CamCrop")

    if crop is None:
        _obs_data = obs.obs_data_create()
        obs.obs_data_set_bool(_obs_data, "relative", True)
        filter = obs.obs_source_create_private("crop_filter", "CamCrop", _obs_data)
        obs.obs_source_filter_add(source, filter)
        obs.obs_source_release(filter)
        obs.obs_data_release(_obs_data)

    settings = obs.obs_source_get_settings(crop)
    i = obs.obs_data_set_int

    i(settings, "left", 20)
    i(settings, "top", 0)
    i(settings, "right", 100)
    i(settings, "bottom", 100)

    obs.obs_source_update(crop, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)
    obs.obs_source_release(crop)

def client_connect():
    global server
    host = 'local host'
    port = 5000

    # create a socket at client side
    # using TCP / IP protocol
    server = socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM)

    # connect it to server and port
    # number on local computer.
    server.connect(('127.0.0.1', port))
def client_response():
    global server_run
    global server
    server.send(str.encode("Ping"))
    msg=server.recv(1024)
    print(msg.decode())
    # while server_run == True:
    #
    # # receive message string from
    #     # server, at a time 1024 B
    #     msg = server.recv(1024)
    #     print('Received:' + msg.decode())
    #     if msg.decode() == "stop":
    #         server_run = False
    #
    #     # repeat as long as message
    #     # string are not empty
    #     # while msg:
    #     #     print('Received:' + msg.decode())
    #     #     msg = server.recv(1024)
    #
    # # disconnect the client
    # server.close()

def refresh_pressed(props, prop):
    crop_cam()
    client_connect()

def receiveMessage(props, prop):
    client_response()

# ------------------------------------------------------------

def script_description():
    return "Connects to the OBSCallMapper for mapping the camera positions in a call to individual sources automatticly in OBS to save time when setting up streams and fixing cameras mid stream" \
           "\n\n By Luna"

def script_update(settings):
    pass

def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "port", 33121)

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_int(props, "port", "Port used to communicate with server. Leave default unless changed in server settings.", 0, 65535, 1)
    obs.obs_properties_add_button(props, "button", "Connect", refresh_pressed)
    obs.obs_properties_add_button(props, "button1", "NextMessage", receiveMessage)
    return props