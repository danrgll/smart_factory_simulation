import random
import simpy
from base_elements import Event
import numpy as np


class Repairman(object):
    def __init__(self, env: simpy.Environment, location, repair_time: tuple):
        """
        :param env: Environment
        :param location: actual location of the person. 2D numpy array.
        :param repair_time: Mean and Sigma time for repair
        """
        self.env = env
        self.busy = False
        self.location = location
        self.repair_time_m_s = repair_time  # processing time

    def work(self, new_job_location, release_resource: Event):
        """Simulates the processing of a repair order. The way to the object and its repair.
        :param new_job_location: location of the job
        :param release_resource: Event which signals the manager to release the resource again.
        """
        time_to_job_location = round(np.linalg.norm(self.location - new_job_location))
        yield self.env.timeout(time_to_job_location)
        self.location = new_job_location
        yield self.env.timeout(self.repair_time())
        self.busy = False
        release_resource.trigger()

    def repair_time(self):
        """return the processing_time"""
        return round(abs(random.normalvariate(self.repair_time_m_s[0], self.repair_time_m_s[1])))
