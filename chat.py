import time
import logging

from typing import Callable
from talon import actions
from dataclasses import dataclass

from .cron_jobs import Job

from listen_to_twitch import Channel
from listen_to_twitch.respond import ResponseManager, Action
from listen_to_twitch.message import Message

class ChatHack:
    active: bool = False
    channel = None

    @classmethod
    def init(cls):
        cls.channel = Channel("ecneicscience")

    @classmethod
    def reset(cls):
        try: cls.channel.close()
        except: pass
        cls.init()

def wrap(func: Callable):
    max_len = 16
    def inner(msg: Message):
        author = msg.author
        if len(author) > max_len:
            author = author[:max_len-3] + "..."
        return func(author)
    return inner

def timed(start_fn: Callable, end_fn: Callable, dur: float = 5):
    def inner(msg: Message):
        wrap(start_fn)(msg)
        print(Job.jobs.keys())
        time.sleep(dur)
        end_fn()
        print(Job.jobs.keys())
    return inner

prefix = "!hack"
au = actions.user

manager = ResponseManager([
    Action(prefix, "run", wrap(au.march_fast)),
    Action(prefix, "walk", wrap(au.march_slow)),
    Action(prefix, "invert", wrap(au.joystick_invert)),
    Action(prefix, "rotate right", wrap(au.joystick_cw)),
    Action(prefix, "rotate left", wrap(au.joystick_ccw)),
    Action(prefix, "straighten", wrap(au.joystick_forward)),
    Action(prefix, "jump", wrap(au.single_jump)),
    Action(prefix, "punch", wrap(au.punch)),
    Action(prefix, "pound", wrap(au.ground_pound)),
    Action(prefix, "camera", wrap(au.camera_toggle)),
    Action(prefix, "zoom in", wrap(au.camera_in)),
    Action(prefix, "zoom out", wrap(au.camera_out)),
    Action(prefix, "cam left", wrap(au.camera_left)),
    Action(prefix, "cam right", wrap(au.camera_right)),
    Action(prefix, "start", wrap(au.press_start)),
    Action(prefix, "pulse left", timed(au.ll_start, au.ll_stop)),
    Action(prefix, "pulse right", timed(au.ll_start, au.ll_stop)),
    Action(prefix, "pulse up", timed(au.whis_hi_start, au.whis_hi_stop)),
    Action(prefix, "pulse down", timed(au.whis_lo_start, au.whis_lo_stop)),
])
    
def process_new_messages():
    for message in ChatHack.channel.new_messages():
        logging.debug(f"{message}")
        manager.process(message)

def clear_old_messages():
    for message in ChatHack.channel.new_messages():
        continue
