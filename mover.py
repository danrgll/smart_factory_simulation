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
        self.events = {
            "reactivate": Event(self.env)
        }
        self.env.process(self.work())

    def transport_update(self, product: Product, pick_up_location: np.array, destination: np.array):
        self.reserved = True
        self.pick_up_location = product.current_location
        self.time_to_pick_up_location = np.linalg.norm(self.location-pick_up_location)  # calculates Euclidean distance
        self.destination = product.next_destination_location
        self.time_to_destination = np.linalg.norm(self.pick_up_location-self.destination)  # calculates Euclidean distance
        self.events["reactivate"].trigger()

    def work(self):
        while True:
            # wait for event that signal mover to work
            yield self.events["reactivate"]
            yield self.env.timeout(self.time_to_pick_up_location)  # time to drive to pick up location
            # ToDo Output Funktion einrichten bei den Resourcen? Lösung
            # ToDo: Event das den Austausch des Produktes irg wie markiert damit Resource losgelassen wird.
            yield self.env.timeout(self.time_to_destination)  # time to drive to destination

