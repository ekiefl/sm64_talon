from talon import cron
from typing import Callable, Dict

class Job:
    jobs = {}

    @classmethod
    def interval(cls, name: str, function: Callable, kwargs: Dict={}, interval: str="34ms"):
        if name in cls.jobs:
            cls.cancel(name)

        routine = lambda: function(**kwargs)
        cls.jobs[name] = cron.interval(interval, routine)

    @classmethod
    def cancel(cls, name):
        assert name in cls.jobs, f"'{name}' is not an active CRON job name."
        job = cls.jobs.pop(name) 
        cron.cancel(job)
