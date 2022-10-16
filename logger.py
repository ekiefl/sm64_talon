import datetime
import numpy as np

from typing import List, Dict
from dataclasses import dataclass

from talon import actions

class Logger:
    def __init__(self, cache_size: int=30):
        self.cache_size = cache_size
        self.events: List[Dict] = [self.null()]

    def last_n(self, n):
        return self.events[-n:]

    def null(self):
        return dict(
            time = datetime.datetime.now(),
            action = None,
            noise = None,
        )

    def add(self, action, noise):
        event = dict(
            time = datetime.datetime.now(),
            action = action,
            noise = noise,
        )

        # Decide whether to report
        if event['action'] == self.events[-1]['action']:
            # This action was reported last. Check if recently
            dt = (event['time'] - self.events[-1]['time']).total_seconds()
            if dt > 0.2:
                self.report(action, noise)
        else:        
            self.report(action, noise)

        self.events.append(event)
        if len(self.events) > self.cache_size:
            self.events = self.events[1:]
        
    def report(self, action, noise):
        if np.random.randint(100) == 1:
            action, noise = "Follow channel", "pls"
        actions.user.noise_log(action, noise)
