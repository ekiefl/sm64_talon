from talon import Module, Context, cron, actions
from dataclasses import dataclass

from .logger import Logger
from .state import GameState, MarioState
from .controller import Controller, key_hold
from .cron_jobs import Job
from .chat import process_new_messages, clear_old_messages, ChatHack

import math
import time

sleep = lambda ms: time.sleep(ms/1000)

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
MARCH_SPEED_1 = 0.5

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
    def march_slow(name: str):
        if not MarioState.marching:
            log.add("Walk", name)
            Controller.LJoy.set_polar(val=MARCH_SPEED_1, angle=MarioState.direction)
        else:
            log.add("Stop", name)
            MarioState.direction = Controller.LJoy.angle
            Controller.LJoy.release()

        MarioState.marching = not MarioState.marching
            
    def march_fast(name: str):
        if not MarioState.marching:
            log.add("Run", name)
            Controller.LJoy.set_polar(val=MARCH_SPEED_2, angle=MarioState.direction)
        else:
            log.add("Stop", name)
            MarioState.direction = Controller.LJoy.angle
            Controller.LJoy.release()

        MarioState.marching = not MarioState.marching
            
    def whis_hi_start(name: str):
        if MarioState.marching:
            # Mario is moving at some speed. Increase that speed
            log.add("Speed up", name)
            Job.interval(
                name = "speed_up",
                function = _bounded_alter_polar,
                kwargs = dict(dr=DELTA_SPEED),
            )
        else:
            # Mario is not moving. Whistling controls Y-axis
            log.add("Pulse up", name)
            Job.interval(
                name = "joy_up",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dy=DELTA_XY),
            )
            
    def whis_lo_start(name: str):
        if MarioState.marching:
            # Mario is moving at some speed. Decrease that speed
            log.add("Slow down", name)
            Job.interval(
                name = "slow_down",
                function = _bounded_alter_polar,
                kwargs = dict(dr=-DELTA_SPEED),
            )
        else:
            # Mario is not moving. Whistling controls Y-axis
            log.add("Pulse down", name)
            Job.interval(
                name = "joy_down",
                function = Controller.LJoy.alter_cartesian,
                kwargs = dict(dy=-DELTA_XY),
            )

    def ll_start(name: str):
        log.add("Pulse left", name)

        if MarioState.marching:
            # Store the current analog stick information, because after the
            # ll interval, the analog stick will be restored
            MarioState.direction = Controller.LJoy.angle
            MarioState.cached_speed = Controller.LJoy.val

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

    def rr_start(name: str):
        log.add("Pulse right", name)

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
            return

        # Cache
        MarioState.direction = Controller.LJoy.angle
        MarioState.cached_speed = 0

        Job.cancel("joy_down")

        if not GameState.sustain_joystick:
            Controller.LJoy.set_polar(
                MarioState.cached_speed,
                MarioState.direction
            )

            Controller.LJoy.release()

    def ll_stop():
        if not MarioState.marching:
            # Set mario's direction where he is looking
            MarioState.direction = Controller.LJoy.angle
            MarioState.cached_speed = 0

        Job.cancel("joy_left")

        # Revert to analog stick state prior to ll interval
        Controller.LJoy.set_polar(
            MarioState.cached_speed,
            MarioState.direction
        )

    def rr_stop():
        if not MarioState.marching:
            # Set mario's direction where he is looking
            MarioState.direction = Controller.LJoy.angle
            MarioState.cached_speed = 0

        Job.cancel("joy_right")

        # Revert to analog stick state prior to ll interval
        Controller.LJoy.set_polar(
            MarioState.cached_speed,
            MarioState.direction
        )

    def joystick_cw(name: str):
        log.add("Rotate right", name)
        Controller.LJoy.alter_polar(dtheta=-DELTA_THETA)
        
    def joystick_ccw(name: str):
        log.add("Rotate left", name)
        Controller.LJoy.alter_polar(dtheta=DELTA_THETA)

    def joystick_forward(name: str):
        log.add("Straighten", name)
        MarioState.direction = 90
        Controller.LJoy.set_polar(
            val=Controller.LJoy.val,
            angle=90,
        )

    def joystick_invert(name: str):
        log.add("Invert", name)
        Controller.LJoy.alter_polar(dtheta=180)
        

@ctx.action_class("user")
class GeneralActions:
    def toggle_sustain(name: str):
        #GameState.sustain_joystick = not GameState.sustain_joystick
        log.add("Nothing", name)

    def single_jump(name: str):
        log.add("Jump", name)
        Controller.A.press(frames=10)

    def punch(name: str):
        if name == "ho" and "pound" in Job.jobs:
            # Ya-ho is often interpreted instead of
            # ya-hoo, which is almost always the intent
            log.add("Jump", name)
            Controller.A.press(frames=10)

        log.add("Punch", name)
        Controller.X.press(frames=10)

    def ground_pound(name: str):
        log.add("Pound", name)
        Controller.LTrig.hold(val=1)
        Job.after(
            name = "pound",
            function = Controller.LTrig.release,
            duration = "500ms",
        )

    def camera_toggle(name: str):
        log.add("Camera", name)
        Controller.RBump.press(frames=2)
        Controller.LJoy.angle = 90
        
    def camera_in(name: str):
        log.add("Zoom in", name)
        Controller.RJoy.set_cartesian(x=0, y=1)
        Job.after(
            name = "zoom_in",
            function = Controller.RJoy.set_cartesian,
            kwargs = dict(x=0, y=0),
            duration = "200ms",
        )
        
    def camera_out(name: str):
        log.add("Zoom out", name)
        Controller.RJoy.set_cartesian(x=0, y=-1)
        Job.after(
            name = "zoom_out",
            function = Controller.RJoy.set_cartesian,
            kwargs = dict(x=0, y=0),
            duration = "200ms",
        )
        
    def camera_left(name: str):
        log.add("Cam left", name)
        Controller.RJoy.set_cartesian(x=-1, y=0)
        Job.after(
            name = "cam_left",
            function = Controller.RJoy.set_cartesian,
            kwargs = dict(x=0, y=0),
            duration = "200ms",
        )
        
    def camera_right(name: str):
        log.add("Cam right", name)
        Controller.RJoy.set_cartesian(x=1, y=0)
        Job.after(
            name = "cam_right",
            function = Controller.RJoy.set_cartesian,
            kwargs = dict(x=0, y=0),
            duration = "200ms",
        )
        
    def exit_lock(name: str):
        # toggle camera (into lakitu)
        Controller.RBump.press(frames=2)
        Controller.LJoy.angle = 90

        # straighten
        MarioState.direction = 90
        Controller.LJoy.set_polar(
            val=Controller.LJoy.val,
            angle=90,
        )

        # outy
        Controller.RJoy.set_cartesian(x=0, y=-1)
        sleep(200)
        Controller.RJoy.set_cartesian(x=0, y=0)

        # let camera equilibrate
        sleep(200)

        # inch forward
        Controller.LJoy.set_cartesian(x=0, y=0.5)
        sleep(200)
        Controller.LJoy.set_cartesian(x=0, y=0)

        # toggle camera (into mario)
        Controller.RBump.press(frames=2)
        Controller.LJoy.angle = 90
        
    def press_start(name: str):
        log.add("Press start", name)
        Controller.Start.press()

    def reset_state(name: str):
        """Call when mario is stationary, in normal lakitu camera mode"""
        MarioState.marching = False
        MarioState.direction = 90
        MarioState.cached_speed = 0
        GameState.sustain_joystick = False
        Controller.LJoy.set_cartesian(x=0, y=0)

    def toggle_chat_hack():
        if ChatHack.active:
            Job.cancel("chat_listen")
            log.add("ChatHack disconnected", "chatty")
        else:
            try:
                ChatHack.reset()
            except:
                log.add("ChatHack failed", "chatty")
                return

            log.add("ChatHack connected", "chatty")
            clear_old_messages()
            Job.interval(
                name = "chat_listen",
                function = process_new_messages,
                interval = "500ms",
            )

        ChatHack.active = not ChatHack.active


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

    def whis_hi_start(name: str):""""""
    def whis_hi_stop():""""""
    def whis_lo_start(name: str):""""""
    def whis_lo_stop():""""""
    def ll_start(name: str):""""""
    def ll_stop():""""""
    def rr_start(name: str):""""""
    def rr_stop():""""""
    def joystick_cw(name: str):""""""
    def joystick_ccw(name: str):""""""
    def joystick_forward(name: str):""""""
    def joystick_invert(name: str):""""""
    def march_fast(name: str):""""""
    def march_slow(name: str):""""""
    def toggle_sustain(name: str):""""""
    def single_jump(name: str):""""""
    def punch(name: str):""""""
    def ground_pound(name: str):""""""
    def press_start(name: str):""""""
    def camera_toggle(name: str):""""""
    def camera_in(name: str):""""""
    def camera_out(name: str):""""""
    def camera_left(name: str):""""""
    def camera_right(name: str):""""""
    def exit_lock(name: str):""""""
    def reset_state(name: str):""""""
    def toggle_chat_hack():""""""


def callback(name: str):
    active = state.pop(name)
    callbacks[name](active)


def on_whis_hi(active: bool):
    if active:
        actions.user.whis_hi_start("high whistle")
    else:
        actions.user.whis_hi_stop()

def on_whis_lo(active: bool):
    if active:
        actions.user.whis_lo_start("low whistle")
    else:
        actions.user.whis_lo_stop()

def on_ll(active: bool):
    if active:
        actions.user.ll_start("ll")
    else:
        actions.user.ll_stop()

def on_rr(active: bool):
    if active:
        actions.user.rr_start("rr")
    else:
        actions.user.rr_stop()

callbacks["whis_hi"] = on_whis_hi
callbacks["whis_lo"] = on_whis_lo
callbacks["ll"] = on_ll
callbacks["rr"] = on_rr
