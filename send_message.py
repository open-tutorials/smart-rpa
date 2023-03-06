from robot import Robot, TOP_RIGHT
import time
import easyocr
import pyautogui

robot = Robot()
robot.step('01_chrome')

robot.keyDown('command')
robot.keyDown('space')
robot.keyUp('space')
robot.keyUp('command')
robot.write('chrome')
robot.press('enter')

time.sleep(2)

robot.step('02_open_tab')

robot.find_by_image('buttons/new_tab.png', TOP_RIGHT).move().click()
robot.past('https://www.esanum.de')
robot.press('enter')

time.sleep(2)

pyautogui.screenshot('esanum_de.png', region=(200, 1350, 1500, 1300))

time.sleep(2)

robot.keyDown('command')
robot.keyDown('w')
robot.keyUp('w')
robot.keyUp('command')

reader = easyocr.Reader(['en'], gpu=True)
found = reader.readtext('esanum_de.png', detail=0, paragraph=True)
contents = found[0]

robot.step('03_send_message')

robot.keyDown('command')
robot.keyDown('space')
robot.keyUp('space')
robot.keyUp('command')
robot.write('slack')
robot.press('enter')

time.sleep(2)

robot.find_by_image('buttons/esanum_in_slack.png').move().click()

robot.keyDown('command')
robot.keyDown('f')
robot.keyUp('f')
robot.keyUp('command')

robot.keyDown('command')
robot.keyDown('a')
robot.keyUp('a')
robot.keyUp('command')

robot.write('Tom')
robot.press('down')
robot.press('down')
robot.press('down')
robot.press('enter')
robot.past(contents)
