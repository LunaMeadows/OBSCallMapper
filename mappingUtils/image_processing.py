"""
Processes a window screenshot and returns cords of all detected cameras
"""
import platform
import os
import time
import pyautogui
from mss import mss
from PIL import Image
import cv2
import numpy as np
if platform.system() == 'Windows':
    import win32gui
elif platform.system() == 'Linux':
    import wmctrl


class ImageProcessing:
    """
    ImageProcessing takes a screenshot of an image using pyautogui and finds the camera rectangles using cv2 and numpy.
    Attributes
    ----------
    windows : array
        array of all visable windows
    camera_pos : array
        array of all the camera positions in the window
    """
    def __init__(self, save_location, debug):
        """
        Sets up global variables for use in code
        """
        self.windows = {}
        self.camera_pos = {}
        self.save_location = str(save_location)
        if not os.path.exists(self.save_location):
            os.makedirs(self.save_location)
        if not os.path.exists(os.path.join(self.save_location, 'cameras')):
            os.makedirs(os.path.join(self.save_location, 'cameras'))
        self.debug = debug

    #TODO Check windows window handling for faster solution
    def __win_enum_handler(self, hwnd, ctx):
        """
        Loops through all visable windows using win32gui and then checks if window has a title.
        If window has title then it will add it to the windows dict. Key is first 28 char of win name and value is win name
        """
        if win32gui.IsWindowVisible( hwnd ):
            if win32gui.GetWindowText(hwnd):
                self.windows[win32gui.GetWindowText(hwnd)[0:28]] = win32gui.GetWindowText(hwnd)


    def get_windows(self):
        """
        If windows system calls the __win_enum_handler and gets all the current visible windows and then returns the windows array
        If Linux system will use WMCTRL to get a list of all current windows and add it to the windows dict. Key is first 28 char of win name and value is win name
        :return: windows
        """
        if(platform.system() == 'Windows'):
            win32gui.EnumWindows(self.__win_enum_handler, None)
        elif(platform.system() == 'Linux'):
            windows_list = wmctrl.Window.list()
            for window in windows_list:
                self.windows[window.wm_name[0:28]] = window.wm_name
        return self.windows
    def get_screenshot(self, window_title):
        """
        Screenshot returns a screenshot of the specified window.
        If windows, uses win32gui to set the window to the foreground and then gets the location of the window and passes it to pyautogui.
        If linux, uses wmctrl to set window to the foreground and then gets the location of the window and passes it to mss
        Pyautogui  then takes the location and takes a screenshot and stores it in the im variable.

        Parameters
        ----------
        window_title : str
            the title of the window that contains the cameras
        """
        if window_title:
            #TODO Test on windows
            if(platform.system() == 'Windows'):
                window_handle = win32gui.FindWindow(None, window_title)
                if window_handle:
                    win32gui.SetForegroundWindow(window_handle)
                    x, y, x1, y1 = win32gui.GetClientRect(window_handle)
                    x, y = win32gui.ClientToScreen(window_handle, (x, y))
                    x1, y1 = win32gui.ClientToScreen(window_handle, (x1 - x, y1 - y))
                    return pyautogui.screenshot(region=(x, y, x1, y1))
                else:
                    raise WindowError("Title provided was not a visable window")
            elif(platform.system() == 'Linux'):
                window_handle = wmctrl.Window.by_name(window_title)[0]
                window_handle.activate()
                #pylint: disable=invalid-name
                x, y, x1, y1 = window_handle.x, window_handle.y, window_handle.x+window_handle.w, window_handle.y+window_handle.h
                time.sleep(1)
                screenshotter = mss()
                for filename in screenshotter.save(output=os.path.join(self.save_location+'/cameras/', 'tempFullScreen.png'), mon=-1):
                    image = Image.open(filename)
                    cropped_image = image.crop((x, y, x1, y1))
                    if not self.debug:
                        os.remove(filename)
                    return cropped_image
        else:
            raise WindowError("Empty string was passed instead of window title")

    def get_exe_name(self, window_title):
        if (platform.system() == 'Windows'):
            pass
        elif (platform.system() == 'Linux'):
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
            #Saves the window image and passes it to cv2 to process camera locations.
            window_img.save(os.path.join(self.save_location+'/cameras/','window.png'))
            process_img = cv2.imread(os.path.join(self.save_location+'/cameras/','window.png'))
            process_img_masked = cv2.imread(os.path.join(self.save_location+'/cameras/','window.png'))

            #Filters image and creates a mask of all black areas to mark out where cameras are
            hsv = cv2.cvtColor(process_img, cv2.COLOR_BGR2HSV)
            background = np.array([0, 0, 0])
            background2 = np.array([1, 1, 1])
            mask = cv2.inRange(hsv, background, background2)
            process_img_masked[mask > 0] = (0, 0, 255)
            kernel = np.ones((5, 5), np.uint8)
            erosion = cv2.erode(mask, kernel, iterations=0)
            edged = cv2.Canny(erosion, 30, 200)


            contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            rects = [cv2.boundingRect(cnt) for cnt in contours]
            rects = sorted(rects, reverse=True)
            index = 0
            y_old = 5000
            x_old = 5000
            cam_area = 0
            #Loops through all rects to figure out camera area
            for rect in rects:
                x_position, y_position, width, height = rect
                area = width * height
                if area > cam_area:
                    cam_area = area

            #Loops through all rects and if camera is detected will save it's location to camera_pos
            for rect in rects:
                x_position, y_position, width, height = rect
                area = width * height
                if area >= cam_area - 2000:
                    if abs(y_old - y_position) > 1 or abs(x_old - x_position > 1):
                        y_old = y_position
                        x_old = x_position
                        x_position, y_position, width, height = rect
                        self.camera_pos[os.path.join(self.save_location+"/cameras/", str(index) + '.jpg')] = [rect, '']
                        out = process_img[y_position + 10:y_position + height-10, x_position + 10:x_position + width-10]
                        if len(out.tobytes()) > 0:
                            cv2.imwrite(os.path.join(self.save_location+"/cameras/", str(index) + '.jpg'), out)
                        index += 1
        if not self.debug:
            os.remove(os.path.join(self.save_location+'/cameras/','window.png'))
        return self.camera_pos


class WindowError(Exception):
    pass
