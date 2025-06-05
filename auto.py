import pyautogui
import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

while True:
    # Mouse move
    x, y = pyautogui.position()
    pyautogui.moveTo(x + 15, y + 15)
    time.sleep(1)
    pyautogui.moveTo(x, y)

    # Keyboard press (Shift key)
    keyboard.press(Key.shift)
    keyboard.release(Key.shift)

    # Wait for 60 seconds
    time.sleep(60)
