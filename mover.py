import simpy
import numpy as np
from base_elements import Event
from product import Product


class Mover(object):
    def __init__(self, env: simpy.Environment, location: np.array):
        self.env = env
        self.location = location  # coordinates of his location
        self.pick_up_location = None
        self.time_to_pick_up_location = None
        self.time_to_destination = None
        self.destination = None
        self.reserved = False  # market whether mover is already in use
        self.start_next_proc_trigger = None
        self.release_resource = None
        self.events = {
            "reactivate": Event(self.env)
        }
        self.env.process(self.work())

    def transport_update(self, product: Product, get_resource, release_resource: Event, start_next_proc_yield: Event, start_next_proc_trigger: Event):
        print("hallo mover")
        self.start_next_proc_trigger = start_next_proc_trigger
        self.release_resource = release_resource
        get_resource.trigger()
        print("g0t_mover")
        yield start_next_proc_yield.event
        print("init mover")
        self.pick_up_location = product.current_location
        self.time_to_pick_up_location = np.linalg.norm(self.location-self.pick_up_location)  # calculates Euclidean distance
        self.destination = product.next_destination_location
        self.time_to_destination = np.linalg.norm(self.pick_up_location-self.destination)  # calculates Euclidean distance
        self.events["reactivate"].trigger()

    def work(self):
        while True:
            # wait for event that signal mover to work
            yield self.events["reactivate"].event
            print("mover föährt los")
            yield self.env.timeout(self.time_to_pick_up_location)  # time to drive to pick up location
            # ToDo Output Funktion einrichten bei den Resourcen? Lösung
            # ToDo: Event das den Austausch des Produktes irg wie markiert damit Resource losgelassen wird.
            yield self.env.timeout(self.time_to_destination)  # time to drive to destination
            self.start_next_proc_trigger.trigger()
            self.reserved = False
            self.release_resource.trigger()
            print("mover angekommen")


