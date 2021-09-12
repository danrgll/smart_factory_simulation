from base_elements import Event
from monitor import MonitorProduct
import simpy
from abc import ABC, abstractmethod

class Product(ABC):
    def __init__(self, env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: dict):
        self.env = env
        self.id = id
        self.proc_steps = proc_steps
        self.time_limit_of_completion = time_limit_completion
        self.properties = properties  # [base_color, [ring_colors], cap_color]
        self.current_location = None
        self.next_destination_location = None
        self.monitor = MonitorProduct(self.env, self.id, proc_steps)  # monitor manufacturing
        self.env.process(self.update_location())
        self.env.process(self.check_points(counter))

    @abstractmethod
    def update_location(self):
        """update location"""
        pass

    def check_points(self, counter):
        yield self.events["proc_completed"].event
        if self.env.now <= self.time_limit_of_completion:
            counter.counter += self.properties["points"]

    def product_infos(self):
        infos = [self.id, self.proc_steps, self.time_limit_of_completion, self.properties]
        return infos




class ProductCC0(Product):
    def __init__(self, env, id, proc_steps,time_limit_completion, counter, properties):
        super().__init__(env, id, proc_steps, time_limit_completion, counter, properties)
        self.stations_location = {"base": None,
                                  "ring": None,
                                  "cap": None,
                                  "del": None
                                  }
        self.events = {"base": Event(self.env),  # events for location change
                       "cap": Event(self.env),
                       "del": Event(self.env),
                       "proc_base": Event(self.env),  # events for process steps
                       "proc_cap": Event(self.env),
                       "proc_del": Event(self.env),
                       "proc_completed": Event(self.env),
                       }

    def update_location(self):
        """update location"""
        yield self.events["base"].event & self.events["cap"].event
        self.current_location = self.stations_location["base"]
        self.next_destination_location = self.stations_location["cap"]
        yield self.events["del"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["del"]


class ProductCCX(Product):
    def __init__(self, env, id, proc_steps,time_limit_completion, counter, properties):
        super().__init__(env, id, proc_steps,time_limit_completion, counter, properties)
        self.stations_location = {"base": None,
                                  "ring": None,
                                  "cap": None,
                                  "del": None
                                  }
        self.events = {"base": Event(self.env),  # events for location change
                       "ring": Event(self.env),
                       "cap": Event(self.env),
                       "del": Event(self.env),
                       "proc_base": Event(self.env),  # events for process steps
                       "proc_ring": Event(self.env),
                       "proc_cap": Event(self.env),
                       "proc_del": Event(self.env),
                       "proc_completed": Event(self.env),
                       }

    def update_location(self):
        """update location"""
        yield self.events["base"].event & self.events["ring"].event
        self.current_location = self.stations_location["base"]
        self.next_destination_location = self.stations_location["ring"]
        yield self.events["cap"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["cap"]
        yield self.events["del"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["del"]



