import pyautogui
import win32gui
import cv2
import numpy as np

def screenshot(window_title=None):
    if window_title:
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            x, y, x1, y1 = win32gui.GetClientRect(hwnd)
            x, y = win32gui.ClientToScreen(hwnd, (x, y))
            x1, y1 = win32gui.ClientToScreen(hwnd, (x1 - x, y1 - y))
            im = pyautogui.screenshot(region=(x, y, x1, y1))
            return im
        else:
            #TODO Create proper error return and list of available windows
            print('Window not found!')
            win32gui.EnumWindows( winEnumHandler, None )
    else:
        print("HOW")
        #TODO Proper else statment

def winEnumHandler( hwnd, ctx ):
    #TODO Proper window enumator handler
    if win32gui.IsWindowVisible( hwnd ):
        print (hex(hwnd), win32gui.GetWindowText( hwnd ))

im = screenshot('General-VOICE')
if im:
    #im.show()
    fileName = ['9', '8', '7', '6', '5', '4', '3', '2', '1', '0']
    im.save('temp.png')
    img = cv2.imread('temp.png')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    kernel = np.ones((5, 5), np.uint8)
    erosion = cv2.erode(gray, kernel, iterations=2)
    kernel = np.ones((4, 4), np.uint8)
    dilation = cv2.dilate(erosion, kernel, iterations=2)

    edged = cv2.Canny(dilation, 30, 200)

    contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rects = [cv2.boundingRect(cnt) for cnt in contours]
    rects = sorted(rects, key=lambda x: x[1], reverse=True)

    i = -1
    j = 1
    y_old = 5000
    x_old = 5000
    for rect in rects:
        x, y, w, h = rect
        area = w * h
        if area > 10000 and area < 100000:
            if abs(y_old - y) > 1:
                y_old = y
                x, y, w, h = rect
                out = img[y + 10:y + h - 10, x + 10:x + w - 10]
                cv2.imwrite('cropped\\' + fileName[i] + '_' + str(j) + '.jpg', out)
                j += 1