import pyautogui
import easyocr
import cv2
import os
import numpy as np
from inflection import underscore
from datetime import datetime
import pyperclip as pc
import platform

DEBUG = True
THRESHOLD = .8
MOUSE_SPEED = .5
TIMEOUT = 20

TOP_LEFT = 1
TOP_RIGHT = 2
BOTTOM_RIGHT = 3
BOTTOM_LEFT = 4
RATIO = 2
INITIAL_RATIO = 2
COMMAND_KEY = 'command'
CACHE_FOLDER = 'cache'


class Point:
    x = None
    y = None

    def __init__(self, x, y):
        self.x = x
        self.y = y


class UiElement:
    x = None
    y = None
    w = None
    h = None
    text = None

    def __init__(self, x, y, w, h, text=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text

    def center(self):
        return Point(self.x + self.w/2, self.y + self.h/2)

    def move(self):
        center = adjust_ratio(self).center()
        pyautogui.moveTo(center.x, center.y, MOUSE_SPEED,
                         pyautogui.easeOutQuad)
        return self

    def click(self):
        pyautogui.click()

    def put(self, image, index):
        cv2.rectangle(image, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), (255, 255, 255), -1)
        cv2.putText(image, str(index), (self.x - 10, self.y + 20),
                    cv2.Formatter_FMT_PYTHON, 0.5, (0, 255, 0), 2)
        if self.text:
            cv2.putText(image, self.text, (self.x, self.y + 20),
                        cv2.Formatter_FMT_PYTHON, 0.8, (0, 255, 0), 2)


def x_sort(e):
    return e.x


def y_sort(e):
    return e.y


def adjust_ratio(box):
    return UiElement(box.x/RATIO, box.y/RATIO, box.w/RATIO, box.h/RATIO)


def sort_elements(elements, direction):
    if direction == TOP_LEFT:
        return sorted(elements, key=x_sort, reverse=False)
    elif direction == TOP_RIGHT:
        return sorted(elements, key=x_sort, reverse=True)
    elif direction == BOTTOM_RIGHT:
        return sorted(elements, key=y_sort, reverse=False)
    elif direction == BOTTOM_LEFT:
        return sorted(elements, key=y_sort, reverse=True)


def find_on_image(source_path, template_path, direction=TOP_LEFT):

    source_image = cv2.imread(source_path)
    template_image = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    w, h = template_image.shape[::-1]

    source_head, source_file = os.path.split(source_path)
    template_head, template_file = os.path.split(template_path)

    source_gray = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
    source_canny = cv2.Canny(source_gray, 100, 200)
    cv2.imwrite(source_head + '/canny_' + source_file, source_canny)

    template_canny = cv2.Canny(template_image, 100, 200)
    cv2.imwrite(template_head + '/canny_' + template_file, template_canny)

    matches = cv2.matchTemplate(source_canny,
                                template_canny, cv2.TM_CCOEFF_NORMED)

    found = np.where(matches >= THRESHOLD)
    found = zip(*found[::-1])

    def map_to_element(e):
        return UiElement(e[0], e[1], w, h)

    elements = list(map(map_to_element, found))
    elements = sort_elements(elements, direction)

    if DEBUG:
        debug_image = source_image.copy()
        index = 1
        for e in elements:
            e.put(debug_image, index)
            index += 1
        debug_source_path = source_head + '/debug_' + source_file
        cv2.imwrite(debug_source_path, debug_image)

    if len(elements) > 0:
        return elements[0]

    return False


def find_text_on_image(source_path, target_text, direction=TOP_LEFT):

    cache_file = underscore(target_text) + '.png'

    source_head, source_file = os.path.split(source_path)

    crop_path = source_head + '/crop_' + cache_file
    if os.path.exists(crop_path):
        return find_on_image(source_path, crop_path, direction)

    reader = easyocr.Reader(['en'], gpu=True)
    found = reader.readtext(source_path, detail=1, paragraph=False)

    def map_to_element(e):
        (box, text, confident) = e
        (top_left, top_right, bottom_right, bottom_left) = box
        x1 = int(top_left[0])
        y1 = int(top_left[1])
        x2 = int(bottom_right[0])
        y2 = int(bottom_right[1])
        return UiElement(x1, y1, x2 - x1, y2 - y1, text)

    elements = list(map(map_to_element, found))
    elements = sort_elements(elements, direction)

    source_image = cv2.imread(source_path)

    if DEBUG:
        ocr_image = source_image.copy()
        index = 1
        for e in elements:
            e.put(ocr_image, index)
            index += 1

        ocr_file = source_head + '/ocr_' + cache_file
        cv2.imwrite(ocr_file, ocr_image)

    target_text = target_text.lower()

    for e in elements:
        if e.text.lower() == target_text:
            crop = source_image[e.y:e.y+e.h, e.x:e.x+e.w]
            cv2.imwrite(crop_path, crop)

            return e

    return False


class Robot:
    step_cache_path = None
    system = platform.system()

    def __init__(self):

        if not os.path.exists(CACHE_FOLDER):
            os.mkdir(CACHE_FOLDER)

    def step(self, name):

        print('step', name)

        step_cache_path = 'cache/' + name
        if not os.path.exists(step_cache_path):
            os.mkdir(step_cache_path)

        self.step_cache_path = step_cache_path
        return self

    def try_find_by_image(self, target_file_path, direction=TOP_LEFT):

        print('try find by image', target_file_path)

        target_head, target_file = os.path.split(target_file_path)

        screen_file = self.step_cache_path + '/screen_' + target_file
        pyautogui.screenshot(screen_file)

        return find_on_image(screen_file, target_file_path, direction)

    def find_by_image(self, target_file_path, direction=TOP_LEFT):

        start = datetime.now()
        while (datetime.now() - start).seconds < TIMEOUT:
            print('.')
            element = self.try_find_by_image(target_file_path, direction)
            if element:
                return element

        raise Exception('Elements not found in timeout')

    def try_find_by_text(self, target_text, direction=TOP_LEFT):

        print('try find by text', target_text)

        cache_file = underscore(target_text) + '.png'

        screen_path = self.step_cache_path + '/screen_' + cache_file
        pyautogui.screenshot(screen_path)

        return find_text_on_image(screen_path, target_text, direction)

    def find_by_text(self, target_text, direction=TOP_LEFT):

        start = datetime.now()
        while (datetime.now() - start).seconds < TIMEOUT:
            print('.')
            element = self.try_find_by_text(target_text, direction)
            if element:
                return element

        raise Exception('Elements not found in timeout')

    def past(sef, text):
        pc.copy(text)
        pyautogui.keyDown(COMMAND_KEY)
        pyautogui.keyDown('a')
        pyautogui.keyUp('a')
        pyautogui.keyUp(COMMAND_KEY)
        pyautogui.keyDown(COMMAND_KEY)
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp(COMMAND_KEY)

    def keyDown(self, key):
        pyautogui.keyDown(key)

    def keyUp(self, key):
        pyautogui.keyUp(key)

    def press(self, key):
        pyautogui.press(key)

    def write(self, text):
        pyautogui.write(text, interval=.05)
