from talon import Module, Context, cron, actions
from dataclasses import dataclass

from .logger import Logger
from .state import GameState, MarioState
from .controller import Controller, key_hold
from .cron_jobs import Job

import math
import time

# -------------------------------------------------------
# Tunables {{{
# -------------------------------------------------------

# Controls the sensitivity that Mario's speed is changed when
# doing on-the-fly whistle speed modification. Measured as
# fraction of analog stick range altered per frame.
DELTA_SPEED = 0.025

# Controls the sensitivity of cardinal analog stick pulsing.
# Measured as fraction of analog stick range altered per frame.
DELTA_XY = 0.07

# The number of degrees the analog stick is rotated during each
# frame of a sss/shh interval
DELTA_THETA = 3.5

# Defines mario's slow speed. Mario's slow speed is the speed
# at which he walks in reponse to a low frequency cluck, and
# also defines the lower limit when doing on-the-fly whistling
MARCH_SPEED_1 = 0.4

# Defines mario's fast speed. Mario's fast speed is the speed
# at which he walks in reponse to a high frequency cluck, and
# also defines the upper limit when doing on-the-fly whistling
MARCH_SPEED_2 = 1.0

# -------------------------------------------------------
# }}}
# -------------------------------------------------------

mod = Module()
log = Logger()

state = {}
cron_jobs = {}
callbacks = {}

ctx = Context()
ctx.matches = r"""
app: sm64
mode: user.single_application
"""

sleep = lambda ms: time.sleep(ms/1000)

def value_from_signal(signal: float, lower: float, upper: float, min_value: int, max_value: int):
    """Returns normalized value based on input signal

    Args:
        lower: Signal level at which min_value is chosen.
        upper: Signal level at which max_value is chosen.
        min_value: Lowest value to be returned.
        max_value: Highest value to be returned.
    """
    if signal < lower: signal = lower
    if signal > upper: signal = upper
    frames_normed = (signal - lower) / (upper - lower)
    frames = math.floor(frames_normed * (max_value - min_value) + min_value)
    return frames


def _bounded_alter_polar(**kwargs):
    """A small wrapper of Controller.LJoy.alter_polar"""
    Controller.LJoy.alter_polar(**kwargs)
    if Controller.LJoy.val > MARCH_SPEED_2:
        Controller.LJoy.val = MARCH_SPEED_2
    if Controller.LJoy.val < MARCH_SPEED_1:
        Controller.LJoy.val = MARCH_SPEED_1
    

@ctx.action_class("user")
class JoyStickActions:
    def march_slow():
        if not MarioState.marching:
            log.add("Slow march", "clook")
            Controller.LJoy.set_polar(val=MARCH_SPEED_1, angle=MarioState.direction)
        else:
            log.add("Stop", "clook")
            MarioState.direction = Controller.LJoy.angle
            Controller.LJoy.release()

        MarioState.marching = not MarioState.marching
            
    def march_fast():
        if not MarioState.marching:
            log.add("March", "cluck")
            Controller.LJoy.set_polar(val=MARCH_SPEED_2, angle=MarioState.direction)
        else:
            log.add("Stop", "cluck")
            MarioState.direction = Controller.LJoy.angle
            Controller.LJoy.release()

        MarioState.marching = not MarioState.marching
            
    def whis_hi_start():
        if MarioState.marching:
            # Mario is moving at some speed. Increase that speed
            log.add("Speed up", "high whistle")
            Job.interval(
                name = "speed_up",
                function = _bounded_alter_polar,
                kwargs = dict(dr=DELTA_SPEED),
            )
        else:
            # Mario is not moving. Whistling controls Y-axis
            log.add("Pulse up", "high whistle")
            Job.interval(
                name = "joy_up",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dy=DELTA_XY),
            )
            
    def whis_lo_start():
        if MarioState.marching:
            # Mario is moving at some speed. Decrease that speed
            log.add("Slow down", "low whistle")
            Job.interval(
                name = "slow_down",
                function = _bounded_alter_polar,
                kwargs = dict(dr=-DELTA_SPEED),
            )
        else:
            # Mario is not moving. Whistling controls Y-axis
            log.add("Pulse down", "low whistle")
            Job.interval(
                name = "joy_down",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dy=-DELTA_XY),
            )

    def ll_start():
        log.add("Pulse left", "ll")

        # Store the current analog stick information, because after the
        # ll interval, the analog stick will be restored
        MarioState.direction = Controller.LJoy.angle
        MarioState.cached_speed = Controller.LJoy.val

        if MarioState.marching:
            Job.interval(
                name = "joy_left",
                function = Controller.LJoy.alter_polar,
                kwargs = dict(dtheta=+DELTA_THETA),
            )
        else:
            Job.interval(
                name = "joy_left",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dx=-DELTA_XY),
            )

    def rr_start():
        log.add("Pulse left", "rr")

        # Store the current analog stick information, because after the
        # rr interval, the analog stick will be restored
        MarioState.direction = Controller.LJoy.angle
        MarioState.cached_speed = Controller.LJoy.val

        if MarioState.marching:
            Job.interval(
                name = "joy_right",
                function = Controller.LJoy.alter_polar,
                kwargs = dict(dtheta=-DELTA_THETA),
            )
        else:
            Job.interval(
                name = "joy_right",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dx=+DELTA_XY),
            )

    def whis_hi_stop():
        if MarioState.marching:
            Job.cancel("speed_up")
        else:
            Job.cancel("joy_up")
            if not GameState.sustain_joystick:
                Controller.LJoy.release()
                # Assuming this is a short whistle to reset mario's direction
                MarioState.direction = 90

    def whis_lo_stop():
        if MarioState.marching:
            Job.cancel("slow_down")
        else:
            Job.cancel("joy_down")
            if not GameState.sustain_joystick:
                Controller.LJoy.release()

    def ll_stop():
        Job.cancel("joy_left")

        # Revert to analog stick state prior to ll interval
        Controller.LJoy.set_polar(
            MarioState.cached_speed,
            MarioState.direction
        )

    def rr_stop():
        Job.cancel("joy_right")

        # Revert to analog stick state prior to ll interval
        Controller.LJoy.set_polar(
            MarioState.cached_speed,
            MarioState.direction
        )

    def joystick_cw():
        log.add("Rotate right", "shush")
        Controller.LJoy.alter_polar(dtheta=-DELTA_THETA)
        
    def joystick_ccw():
        log.add("Rotate left", "hiss")
        Controller.LJoy.alter_polar(dtheta=DELTA_THETA)

    def joystick_forward():
        log.add("Straighten", "kk")
        Controller.LJoy.alter_polar(dtheta=-Controller.LJoy.angle+90)
        

@ctx.action_class("user")
class GeneralActions:
    def toggle_sustain():
        #GameState.sustain_joystick = not GameState.sustain_joystick
        log.add("Nothing", "pop")

    def single_jump():
        log.add("Jump", "wa")
        Controller.A.press(frames=10)

    def camera_toggle():
        Controller.RBump.press(frames=2)
        Controller.LJoy.angle = 90
        
    def press_start():
        Controller.Start.press()

    def reset_state():
        """Call when mario is stationary, in normal lakitu camera mode"""
        MarioState.marching = False
        MarioState.direction = 90
        MarioState.cached_speed = 0
        GameState.sustain_joystick = False


@mod.action_class
class Actions:
    def noise_log(action: str, noise: str):
        """Add to log"""
        actions.user.hud_add_log("command", "<*" + action + "/> «" + noise + "»")

    def noise_debounce(name: str, active: bool):
        """Start or stop continuous noise using debounce"""
        if name not in state:
            state[name] = active
            cron_jobs[name] = cron.after("60ms", lambda: callback(name))
        elif state[name] != active:
            cron.cancel(cron_jobs[name])
            state.pop(name)

    def whis_hi_start():""""""
    def whis_hi_stop():""""""
    def whis_lo_start():""""""
    def whis_lo_stop():""""""
    def ll_start():""""""
    def ll_stop():""""""
    def rr_start():""""""
    def rr_stop():""""""
    def joystick_cw():""""""
    def joystick_ccw():""""""
    def joystick_forward():""""""
    def march_fast():""""""
    def march_slow():""""""
    def toggle_sustain():""""""
    def single_jump():""""""
    def press_start():""""""
    def camera_toggle():""""""
    def reset_state():""""""


def callback(name: str):
    active = state.pop(name)
    callbacks[name](active)


def on_whis_hi(active: bool):
    if active:
        actions.user.whis_hi_start()
    else:
        actions.user.whis_hi_stop()

def on_whis_lo(active: bool):
    if active:
        actions.user.whis_lo_start()
    else:
        actions.user.whis_lo_stop()

def on_ll(active: bool):
    if active:
        actions.user.ll_start()
    else:
        actions.user.ll_stop()

def on_rr(active: bool):
    if active:
        actions.user.rr_start()
    else:
        actions.user.rr_stop()

callbacks["whis_hi"] = on_whis_hi
callbacks["whis_lo"] = on_whis_lo
callbacks["ll"] = on_ll
callbacks["rr"] = on_rr
