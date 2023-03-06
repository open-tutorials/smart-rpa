from robot import Robot

robot = Robot()
robot.step('01_open_settings')
robot.find_by_image('buttons/vs_open_settings.png').move().click()

robot.step('02_open_extensions')
robot.find_by_text('extensions').move().click()

robot.step('03_find_go_nightly')
robot.past('go lang')
robot.find_by_text('go nightly').move().click()
