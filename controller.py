from talon import Context
from dataclasses import dataclass

import vgamepad as vg
import math
import time
import numpy as np

ctx = Context()
ctx.matches = r"""
app: sm64
mode: user.single_application
"""

gamepad = vg.VX360Gamepad()

key_hold: float = 34
sleep = lambda ms: time.sleep(ms/1000)

@dataclass
class Button:
    _id: vg.XUSB_BUTTON
    held: bool = False

    def press(self, frames: int=1):
        assert frames > 0
        self.hold()
        sleep(key_hold * frames)
        self.release()

    def hold(self):
        gamepad.press_button(self._id)
        gamepad.update()
        self.held = True

    def release(self):
        gamepad.release_button(self._id)
        gamepad.update()
        self.held = False


@dataclass
class Trigger:
    side: str
    held: bool = False

    def get_trigger(self):
        if self.side == 'left':
            return gamepad.left_trigger
        elif self.side == 'right':
            return gamepad.right_trigger
        else:
            raise ValueError

    def press(self, val: float, frames: int=1):
        """Value between 0 and 1"""
        assert frames > 0
        self.hold(val)
        sleep(key_hold * frames)
        self.release()

    def hold(self, val: float):
        """Value between 0 and 1"""
        val = self._convert(val)
        self.get_trigger()(value=val)
        gamepad.update()
        self.held = True

    def release(self):
        self.get_trigger()(value=0)
        gamepad.update()
        self.held = False

    def _convert(self, val: float) -> int:
        """Convert fraction to 0-255 integer range"""
        return int(math.floor(val*255))


@dataclass
class JoyStick:
    side: str
    val: float = 0
    angle: float = 0
    active: bool = False

    def get_joystick(self):
        if self.side == 'left':
            return gamepad.left_joystick_float
        elif self.side == 'right':
            return gamepad.right_joystick_float
        else:
            raise ValueError

    def set_polar(self, val: float, angle: float):
        """val between 0 and 1, and angle in degrees [0,360] (right is 0)"""
        x, y = self._convert_polar(val, angle)
        self.get_joystick()(x_value_float=x, y_value_float=y)        
        gamepad.update()
        self.val = val
        self.angle = angle
        self.active = True

    def set_cartesian(self, x: float, y: float):
        """x and y between 0 and 1. Behavior when sqrt(x^2+y^2)>1 unknown"""
        # normalize vector to 1
        x, y = self._convert_polar(*self._convert_cartesian(x, y))
        self.get_joystick()(x_value_float=x, y_value_float=y)        
        gamepad.update()
        self.val, self.angle = self._convert_cartesian(x, y)
        self.active = True

    def alter_polar(self, dr: float = 0, dtheta: float = 0):
        """Change state based on current state"""
        if self.val + dr < 0:
            dr = self.val

        self.set_polar(val=self.val+dr, angle=self.angle+dtheta)

    def alter_cartesian(self, dx: float = 0, dy: float = 0):
        """Change state based on current state"""
        curr_x, curr_y = self._convert_polar(self.val, self.angle)
        self.set_cartesian(x=curr_x+dx, y=curr_y+dy)

    def release(self):
        self.get_joystick()(x_value_float=0, y_value_float=0)
        gamepad.update()
        self.val = 0
        self.angle = 90
        self.active = False

    def _convert_polar(self, val: float, angle: float):
        if val > 1:
            val = 1
        rads = math.pi/180 * angle
        return val*math.cos(rads), val*math.sin(rads)
        
    def _convert_cartesian(self, x: float, y: float):
        angle = np.arctan2(y, x) * 180/np.pi # degrees
        if (val := np.sqrt(x**2 + y**2)) > 1: val = 1
        return val, angle
        

class Controller:
    A: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    B: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    X: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    Y: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

    DUp: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
    DRight: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
    DDown: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
    DLeft: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

    Start: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
    Back: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
    Guide: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)

    LBump: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
    RBump: Button = Button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    LTrig: Trigger = Trigger("left")
    RTrig: Trigger = Trigger("right")

    LJoy: JoyStick = JoyStick("left")
    RJoy: JoyStick = JoyStick("right")
