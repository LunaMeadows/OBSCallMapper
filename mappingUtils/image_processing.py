"""
Processes a window screenshot and returns cords of all detected cameras
"""
import platform
import os
import time
from mss import mss
from PIL import Image
import cv2
import numpy as np

if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes, cdll, CFUNCTYPE, c_bool, POINTER, c_int, create_unicode_buffer
    import psutil
elif platform.system() == 'Linux':
    import wmctrl


class ImageProcessing:
    """
    ImageProcessing takes a screenshot of an image using mss and finds the camera rectangles using cv2 and numpy.
    Attributes
    ----------
    windows : array
        array of all visable windows
    camera_pos : array
        array of all the camera positions in the window
    save_location : str
        Location of saved screenshots
    debug : bool
        Enables debugging for easy troubleshooting

    """

    def __init__(self, save_location, debug = False):
        self.windows = {}
        self.camera_pos = {}
        self.save_location = str(os.path.join(save_location, 'cameras'))
        if not os.path.exists(self.save_location):
            os.makedirs(os.path.join(self.save_location, 'cameras'))
        self.debug = debug
        if platform.system() == 'Windows':
            self.EnumWindows = cdll.user32.EnumWindows
            self.EnumWindowsProc = CFUNCTYPE(c_bool, POINTER(c_int), POINTER(c_int))
            self.GetWindowText = cdll.user32.GetWindowTextW
            self.GetWindowTextLength = cdll.user32.GetWindowTextLengthW
            self.IsWindowVisible = cdll.user32.IsWindowVisible
            self.FindWindow = cdll.user32.FindWindowW
            self.SetForegroundWindow = cdll.user32.SetForegroundWindow
            self.GetWindowRect = cdll.user32.GetWindowRect
            self.GetClassName = cdll.user32.GetClassNameW
            self.GetWindowThreadProcessId = cdll.user32.GetWindowThreadProcessId

    def __win_enum_handler(self, hwnd, ctx):
        """
        Loops through all visable windows using ctypes and then checks if window has a title.
        If window has title then it will add it to the windows dict. Key is first 28 char of win name and value is win name
        """
        if self.IsWindowVisible(hwnd):
            length = self.GetWindowTextLength(hwnd)
            buff = create_unicode_buffer(length + 1)
            self.GetWindowText(hwnd, buff, length + 1)
            is_cloaked = c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
            if buff.value and is_cloaked.value == 0:
                self.windows[buff.value[0:28]] = buff.value

    def get_windows(self):
        """
        If windows system calls the __win_enum_handler and gets all the current visible windows and then returns the windows array
        If Linux system will use WMCTRL to get a list of all current windows and add it to the windows dict. Key is first 28 char of win name and value is win name
        :return: windows
        """
        if platform.system() == 'Windows':
            self.EnumWindows(self.EnumWindowsProc(self.__win_enum_handler), 0)
        elif platform.system() == 'Linux':
            windows_list = wmctrl.Window.list()
            for window in windows_list:
                self.windows[window.wm_name[0:28]] = window.wm_name
        else:
            return
        return self.windows

    def get_screenshot(self, window_title):
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
        if window_title:
            if platform.system() == 'Windows':
                window_handle = self.FindWindow(None, window_title)
                if window_handle:
                    self.SetForegroundWindow(window_handle)
                    window_rect = wintypes.RECT()
                    self.GetWindowRect(window_handle, ctypes.pointer(window_rect))
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
                else:
                    raise WindowError("Title provided was not a visable window")
            elif platform.system() == 'Linux':
                window_handle = wmctrl.Window.by_name(window_title)[0]
                window_handle.activate()
                x, y, x1, y1 = window_handle.x, window_handle.y, window_handle.x + window_handle.w, window_handle.y + window_handle.h
                time.sleep(1)
                screenshotter = mss()
                for filename in screenshotter.save(output=os.path.join(self.save_location, 'tempFullScreen.png'),mon=-1):
                    image = Image.open(filename)
                    cropped_image = image.crop((x, y + 20, x1, y1))
                    if not self.debug:
                        os.remove(filename)
                    return cropped_image
            else:
                return
        else:
            raise WindowError("Empty string was passed instead of window title")

    def get_exe_name(self, window_title):
        """
        Returns a formated string for use with OBS
        :param window_title:
        :return: str
        """
        if platform.system() == 'Windows':
            window_handle = self.FindWindow(None, window_title)
            class_name = ctypes.create_unicode_buffer(36)
            self.GetClassName(window_handle, class_name, 36)
            pid = ctypes.c_ulong()
            self.GetWindowThreadProcessId(window_handle, ctypes.byref(pid))
            exe = psutil.Process(pid.value).name()
            return "{id}:{title}:{exe}".format(id=window_title, title=class_name.value, exe=exe)
        if platform.system() == 'Linux':
            window = wmctrl.Window.by_name(window_title)[0]
            return "{id}\r\n{title}\r\n{exe}".format(id=int(window.id, 16), title=window.wm_name, exe=window.wm_class.split('.')[0])

    def get_camera_pos(self, window_title):
        """
        Returns the camera positions from the provided window in an array.
        Each position contains the x and y of the top left corner and the width and height of each camera.

        Parameters
        ----------
        window_title : str
            the title of the window that contains the cameras
        debug : bool
            if True then the image of the window as well as each camera crop will be stored for debuging useage.

        :return: array of camera positions (x,y,width,height)
        """
        window_img = self.get_screenshot(window_title)
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
                        self.camera_pos[os.path.join(self.save_location, str(index) + '.jpg')] = [rect, '']

                        out = process_img[y_position + 10:y_position + height - 10,
                              x_position + 10:x_position + width - 10]
                        if len(out.tobytes()) > 0:
                            cv2.imwrite(os.path.join(self.save_location, str(index) + '.jpg'), out)
                        index += 1
        if not self.debug:
            os.remove(os.path.join(self.save_location, 'window.png'))
        return self.camera_pos


class WindowError(Exception):
    pass
