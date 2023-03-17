"""
Processes a window screenshot and returns cords of all detected cameras
"""
import platform  # Used to get platform system of the user
import os  # used for file manipulation and data paths
import time  # Used to wait between showing a window and grabbing a screenshot
from typing import Dict, List, Union  # Used for typing

from mss import mss  # Used to get screenshot of the users whole computer
from PIL import Image  # Used for loading and manipulating images
import cv2  # Used for getting camera locations
import numpy as np  # Used to assist with getting camera locations

if platform.system() == 'Windows':
    import ctypes  # Used to get window information
    from ctypes import wintypes, cdll, CFUNCTYPE, c_bool, POINTER, c_int, create_unicode_buffer
    import psutil
elif platform.system() == 'Linux':
    import wmctrl  # Used to get window information


class ImageProcessing:
    """
    ImageProcessing takes a screenshot of an image using mss and finds the camera rectangles using cv2 and numpy.
    Attributes
    ----------
    windows : dict
        dictionary of window names with the key being the name shrunk to fit in a toga selection widget and the value being the full name
    camera_pos : dict
        dictionary of all the cameras in the window. Key is the screenshot file and the value is a list of the position rect and a blank string
    save_location : str
        Location of saved screenshots
    debug : bool
        Enables debugging for easy troubleshooting
    """
    windows: Dict[str, str]
    cameras: Dict[str, List[Union[list, str]]]
    save_location: str
    debug: bool

    def __init__(self, save_location: str, debug: bool = False):
        self.windows = {}
        self.cameras = {}
        # Checks to see if a location for storing camera screenshots is created and if not creates it
        self.save_location = str(os.path.join(save_location, 'cameras'))
        if not os.path.exists(self.save_location):
            os.makedirs(os.path.join(self.save_location, 'cameras'))
        self.debug = debug

    def toggle_debugging(self):
        """
        Toggles on or off debugging
        """
        if self.debug:
            self.debug = False
        else:
            self.debug = True

    def __win_enum_handler(self, hwnd, _):
        """
        Loops through all visable windows using ctypes and then checks if window has a title.
        If window has title then it will add it to the windows dict. Key is first 28 char of win name and value is win name
        """
        get_window_text = cdll.user32.GetWindowTextW
        get_window_text_length = cdll.user32.GetWindowTextLengthW
        is_window_visible = cdll.user32.IsWindowVisible
        # Checks to see if the window is hidden or not and if not will get window title
        if is_window_visible(hwnd):
            length = get_window_text_length(hwnd)
            buff = create_unicode_buffer(length + 1)
            get_window_text(hwnd, buff, length + 1)
            is_cloaked = c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
            if buff.value and is_cloaked.value == 0:
                self.windows[buff.value[0:28]] = buff.value

    def get_windows(self) -> Dict[str, str]:
        """
        If windows system calls the __win_enum_handler and gets all the current visible windows and then returns the windows array
        If Linux system will use WMCTRL to get a list of all current windows and add it to the windows dict. Key is first 28 char of win name and value is win name
        :return: windows
        """
        if platform.system() == 'Windows':
            enum_windows = cdll.user32.EnumWindows
            enum_windows_proc = CFUNCTYPE(c_bool, POINTER(c_int), POINTER(c_int))
            enum_windows(enum_windows_proc(self.__win_enum_handler), 0)
        elif platform.system() == 'Linux':
            windows_list = wmctrl.Window.list()
            for window in windows_list:
                self.windows[window.wm_name[0:28]] = window.wm_name
        else:
            return {}
        return self.windows

    def get_screenshot(self, window_title: str) -> Image:
        # pylint: disable=invalid-name
        """
        Screenshot returns a screenshot of the specified window.
        If windows, uses ctypes to set the window to the foreground and then gets the location of the window and passes it to mss.
        If linux, uses wmctrl to set window to the foreground and then gets the location of the window and passes it to mss
        Parameters
        ----------
        window_title : str
            the title of the window that contains the cameras
        """
        if platform.system() == 'Windows':
            find_window = cdll.user32.FindWindowW
            window_handle = find_window(None, window_title)
            if window_handle:
                set_foreground_window = cdll.user32.SetForegroundWindow
                set_foreground_window(window_handle)
                window_rect = wintypes.RECT()
                get_window_rect = cdll.user32.GetWindowRect
                get_window_rect(window_handle, ctypes.pointer(window_rect))
                x, y, x1, y1 = window_rect.left, window_rect.top, window_rect.right, window_rect.bottom
                time.sleep(1)
                screenshotter = mss()
                for filename in screenshotter.save(
                        output=os.path.join(self.save_location, 'tempFullScreen.png'), mon=-1):
                    image = Image.open(filename)
                    cropped_image = image.crop((x, y, x1, y1))
                    if not self.debug:
                        os.remove(filename)
                    return cropped_image
        elif platform.system() == 'Linux':
            window_handle = wmctrl.Window.by_name(window_title)[0]
            window_handle.activate()
            x, y, x1, y1 = window_handle.x, window_handle.y, window_handle.x + window_handle.w, window_handle.y + window_handle.h
            time.sleep(1)
            screenshotter = mss()
            for filename in screenshotter.save(output=os.path.join(self.save_location, 'tempFullScreen.png'),
                                               mon=-1):
                image = Image.open(filename)
                cropped_image = image.crop((x, y + 20, x1, y1))
                if not self.debug:
                    os.remove(filename)
                return cropped_image
        else:
            return

    def get_exe_name(self, window_title: str) -> str:
        """
        Returns a formatted string for use with OBS
        :param window_title:
        :return: str
        """
        if platform.system() == 'Windows':
            find_window = cdll.user32.FindWindowW
            window_handle = find_window(None, window_title)
            class_name = ctypes.create_unicode_buffer(36)
            get_class_name = cdll.user32.GetClassNameW
            get_class_name(window_handle, class_name, 36)
            pid = ctypes.c_ulong()

            get_window_thread_process_id = cdll.user32.GetWindowThreadProcessId
            get_window_thread_process_id(window_handle, ctypes.byref(pid))
            exe = psutil.Process(pid.value).name()
            return "{id}:{title}:{exe}".format(id=window_title, title=class_name.value, exe=exe)
        if platform.system() == 'Linux':
            window = wmctrl.Window.by_name(window_title)[0]
            return "{id}\r\n{title}\r\n{exe}".format(id=int(window.id, 16), title=window.wm_name,
                                                     exe=window.wm_class.split('.')[0])

    def get_camera_pos(self, window_title: str, screenshot: str = None) -> dict:
        """
        Returns the camera positions from the provided window in an array.
        Each position contains the x and y of the top left corner and the width and height of each camera.

        Parameters
        ----------
        window_title : str
            the title of the window that contains the cameras
        debug : bool
            if True then the image of the window as well as each camera crop will be stored for debugging usage.

        :return: array of camera positions (x,y,width,height)
        """
        if not screenshot:
            window_img = self.get_screenshot(window_title)
        else:
            window_img = Image.open(screenshot)
        if window_img:
            # Saves the window image and passes it to cv2 to process camera locations.
            window_img.save(os.path.join(self.save_location, 'window.png'))
            process_img = cv2.imread(os.path.join(self.save_location, 'window.png'))
            process_img_masked = cv2.imread(os.path.join(self.save_location, 'window.png'))

            # Filters image and creates a mask of all black areas to mark out where cameras are
            hsv = cv2.cvtColor(process_img, cv2.COLOR_BGR2HSV)
            background = np.array([0, 0, 0])
            background2 = np.array([1, 1, 1])
            mask = cv2.inRange(hsv, background, background2)
            process_img_masked[mask > 0] = (0, 0, 255)
            kernel = np.ones((5, 5), np.uint8)
            erosion = cv2.erode(mask, kernel, iterations=0)
            edged = cv2.Canny(erosion, 30, 200)

            if self.debug:
                cv2.imwrite(os.path.join(self.save_location, 'mask.png'), mask)
                cv2.imwrite(os.path.join(self.save_location, 'processed_image.png'), process_img_masked)
                cv2.imwrite(os.path.join(self.save_location, 'erosion.png'), erosion)
                cv2.imwrite(os.path.join(self.save_location, 'edged.png'), edged)

            contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            rects = [cv2.boundingRect(cnt) for cnt in contours]
            rects = sorted(rects, reverse=True)
            index = 0
            y_old = 5000
            x_old = 5000
            cam_area = 0
            # Loops through all rects to figure out camera area
            for rect in rects:
                x_position, y_position, width, height = rect
                area = width * height
                if area > cam_area and width < process_img.shape[1] - 150:
                    cam_area = area

            # Loops through all rects and if camera is detected will save it's location to camera_pos
            for rect in rects:
                x_position, y_position, width, height = rect
                area = width * height
                if area == cam_area:
                    if abs(y_old - y_position) > 1 or abs(x_old - x_position > 1):
                        y_old = y_position
                        x_old = x_position
                        x_position, y_position, width, height = rect
                        self.cameras[os.path.join(self.save_location, str(index) + '.jpg')] = [rect, '']

                        out = process_img[y_position + 10:y_position + height - 10,
                              x_position + 10:x_position + width - 10]
                        if len(out.tobytes()) > 0:
                            cv2.imwrite(os.path.join(self.save_location, str(index) + '.jpg'), out)
                        index += 1
        if not self.debug:
            os.remove(os.path.join(self.save_location, 'window.png'))
        return self.cameras
