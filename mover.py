import simpy
import numpy as np
from base_elements import Event
from product import Product
import random


class Mover(object):
    """Functions as a transport unit which moves products from A to B. Loading times and transport
     times are taken into account."""
    def __init__(self, env: simpy.Environment, id, location: np.array, time_to_pick_up: tuple):
        """

        :param env: Environment
        :param id: mover id
        :param location: location from mover
        :param time_to_pick_up: (mean and sigma) for pickup time of a product
        """
        self.env = env
        self.id = id
        self.location = location  # coordinates of his location
        self.pick_up_location = None
        self.time_to_pick_up_location = None
        self.time_to_pick_up_m_s = time_to_pick_up
        self.time_to_destination = None
        self.destination = None
        self.reserved = False  # market whether mover is already in use
        self.start_next_proc_trigger = None
        self.release_resource = None
        self.events = {
            "reactivate": Event(self.env)
        }
        self.env.process(self.work())
        self.current_product = None
        self.proc_alive = None

    def transport_update(self, proc_id, product: Product, get_resource: Event, release_resource: Event,
                         start_next_proc_yield: Event, start_next_proc_trigger: Event, new_try: Event,
                         proc_succeed: Event):
        """Waits until the product is ready for transport and all necessary transport information is available.
        The transport process is then triggered. While waiting, the mover can be removed from the product and the
         process is interrupted.

         :param get_resource: Event which signals to the process that it has received the mover
         :param release_resource: Event that releases the mover as a resource again
         :param start_next_proc_yield: Event which signals the start of the mover's activity
         :param start_next_proc_trigger: Event that sets the next sub-process in motion
         :param new_try: Event which signals to the manager that the process is being deprived of the resource and
         must request it again.
         :param proc_succeed: Event which signals the successful completion of the resource and its work.
         """
        try:
            self.current_product = product
            self.proc_alive = proc_succeed
            product.monitor.monitor("BEREIT FÜR TRANSPORT", self.env.now, "mover", self.id)
            self.start_next_proc_trigger = start_next_proc_trigger
            self.release_resource = release_resource
            get_resource.trigger()
            yield start_next_proc_yield.event
            if product.events["new_location"].event.triggered is not True:
                yield product.events["new_location"].event
            self.pick_up_location = product.current_location
            # calculates Euclidean distance
            self.time_to_pick_up_location = round(np.linalg.norm(self.location-self.pick_up_location))
            self.destination = product.next_destination_location
            # calculates Euclidean distance
            self.time_to_destination = round(np.linalg.norm(self.pick_up_location-self.destination))
            product.events["new_location"] = Event(self.env, False)
            self.events["reactivate"].trigger()

        except simpy.Interrupt:
            product.monitor.monitor("UNTERBROCHEN", self.env.now, "mover", self.id)
            self.reserved = False
            new_try.trigger()
            return

    def work(self):
        """Simulates the transport process from pickup location to destination. After delivery, it is signalled
        that the resource is to be released again and the next process step is triggered, if available."""
        while True:
            # wait for event that signal mover to work
            yield self.events["reactivate"].event
            self.current_product.monitor.monitor("STARTE TRANSPORT", self.env.now, "mover")
            yield self.env.timeout(self.time_to_pick_up_location*4)  # time to drive to pick up location 1m=4s
            yield self.env.timeout(self.time_to_pick_up())
            yield self.env.timeout(self.time_to_destination*4)  # time to drive to destination 1m=4s
            yield self.env.timeout(self.time_to_pick_up())
            self.location = self.destination
            self.proc_alive.trigger()
            self.start_next_proc_trigger.trigger()
            self.reserved = False
            self.release_resource.trigger()
            self.current_product.monitor.monitor("FERTIG", self.env.now, "mover")

    def time_to_pick_up(self):
        """Returns pick up time"""
        return round(abs(random.normalvariate(self.time_to_pick_up_m_s[0], self.time_to_pick_up_m_s[1])))
