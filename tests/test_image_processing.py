import pytest
from mappingUtils import image_processing
import os
from PIL import Image

def test_get_windows_dict():
    ip = image_processing.ImageProcessing(os.getcwd(), False)
    assert type(ip.get_windows()) == dict

def test_get_screenshot_no_window():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    with pytest.raises(image_processing.WindowError):
        ip.get_screenshot('')

def test_get_screenshot_window_does_not_exist():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    with pytest.raises(IndexError):
        ip.get_screenshot('Cows')

def test_get_screenshot_window_exists_debug_on():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    assert type(ip.get_screenshot('#general | BeeWare - Discord')) == Image.Image

def test_get_screenshot_window_exists_debug_off():
    ip = image_processing.ImageProcessing(os.getcwd(), False)
    assert type(ip.get_screenshot('#general | BeeWare - Discord')) == Image.Image

def test_get_camera_pos_window_exists_debug_off():
    ip = image_processing.ImageProcessing(os.getcwd(), False)
    assert type(ip.get_camera_pos('General')) == dict

def test_get_camera_pos_window_exists_debug_on():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    assert type(ip.get_camera_pos('General')) == dict

def test_get_camera_pos_window_does_not_exist():
    ip = image_processing.ImageProcessing(os.getcwd(), False)
    with pytest.raises(IndexError):
        ip.get_camera_pos('Cows')

def test_get_exe_name_window_exists():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    assert type(ip.get_exe_name('General')) == str

def test_get_exe_name_window_does_not_exists():
    ip = image_processing.ImageProcessing(os.getcwd(), True)
    with pytest.raises(IndexError):
        ip.get_exe_name('Cows')[0]



