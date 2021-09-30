import simpy
import numpy as np
from base_elements import Event
from product import Product
import random


class Mover(object):
    def __init__(self, env: simpy.Environment, id, location: np.array, time_to_pick_up: tuple):
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

    def transport_update(self,proc_id, product: Product, get_resource, release_resource: Event, start_next_proc_yield: Event, start_next_proc_trigger: Event, new_try):
        try:
            self.current_product = product
            product.monitor.monitor("BEREIT FÜR TRANSPORT", self.env.now, "mover")
            self.start_next_proc_trigger = start_next_proc_trigger
            self.release_resource = release_resource
            get_resource.trigger()
            yield start_next_proc_yield.event
            if product.events["new_location"].event.triggered is not True:
                yield product.events["new_location"].event
            print(f"mover {self.id}, drive product {product.product_infos()}")
            self.pick_up_location = product.current_location
            self.time_to_pick_up_location = np.linalg.norm(self.location-self.pick_up_location)  # calculates Euclidean distance
            self.destination = product.next_destination_location
            self.time_to_destination = np.linalg.norm(self.pick_up_location-self.destination)  # calculates Euclidean distance
            product.events["new_location"] = Event(self.env, False)
            self.events["reactivate"].trigger()

        except simpy.Interrupt:
            product.monitor.monitor("UNTERBROCHEN", self.env.now, "mover")
            #if product.processes[proc_id].got_all_resources is True:
                #return Exception
            self.reserved = False
            new_try.trigger()
            return

    def work(self):
        while True:
            # wait for event that signal mover to work
            yield self.events["reactivate"].event
            self.current_product.monitor.monitor("STARTE TRANSPORT", self.env.now, "mover")
            yield self.env.timeout(self.time_to_pick_up_location*4)  # time to drive to pick up location 1m=4s
            # ToDo Output Funktion einrichten bei den Resourcen? Lösung
            yield self.env.timeout(self.time_to_pick_up())
            # ToDo: Event das den Austausch des Produktes irg wie markiert damit Resource losgelassen wird.
            yield self.env.timeout(self.time_to_destination*4)  # time to drive to destination 1m=4s
            self.location = self.destination
            self.start_next_proc_trigger.trigger()
            self.reserved = False
            self.release_resource.trigger()
            self.current_product.monitor.monitor("FERTIG", self.env.now, "mover")

    def time_to_pick_up(self):
        return abs(random.normalvariate(self.time_to_pick_up_m_s[0], self.time_to_pick_up_m_s[1]))


