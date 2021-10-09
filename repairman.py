import random
import simpy
from base_elements import Event
import numpy as np


class Repairman(object):
    def __init__(self, env: simpy.Environment, location, repair_time: tuple):
        self.env = env
        self.busy = False
        self.location = location
        self.repair_time_m_s = repair_time

    def work(self, new_job_location, release_resource: Event):
        # time to arrive broken machine
        time_to_job_location = round(np.linalg.norm(self.location - new_job_location))
        yield self.env.timeout(time_to_job_location)
        self.location = new_job_location
        yield self.env.timeout(self.repair_time())
        self.busy = False
        release_resource.trigger()

    def repair_time(self):
        """return the processing_time"""
        return round(abs(random.normalvariate(self.repair_time_m_s[0], self.repair_time_m_s[1])))


