from base_elements import Event
from monitor import MonitorProduct
import simpy
from abc import ABC, abstractmethod


class Product(ABC):
    def __init__(self, env: simpy.Environment, id: int, counter, properties: dict):
        """
        :param env: Environment
        :param id: Product id
        :param counter: counter which counts the global points achieved
        :param properties: properties of the product like base, ring and cap color saved in a dict.
        """
        self.env = env
        self.id = id
        self.properties = properties
        self.proc_steps = properties["proc_steps"]
        self.time_limit_of_completion = properties["time"]
        self.properties = properties  # [base_color, [ring_colors], cap_color]
        self.current_location = None
        self.next_destination_location = None
        self.processes = dict()
        self.monitor = MonitorProduct(self.env, self.id)  # monitor manufacturing
        self.env.process(self.update_location())
        self.env.process(self.check_points(counter))

    @abstractmethod
    def update_location(self):
        """update location"""
        pass

    def check_points(self, counter):
        """Method is used to evaluate the achieved number of points after completion of its processes and
        to pass them to the counter."""
        yield self.events["proc_completed"].event
        if self.env.now <= self.time_limit_of_completion:
            counter.counter += self.properties["points"]
        elif self.env.now <= self.time_limit_of_completion+10:
            counter.counter += ((self.properties["points"]*80)/100)
        elif self.env.now <= self.time_limit_of_completion+20:
            counter.counter += ((self.properties["points"] * 10) / 100)

    def product_infos(self):
        infos = (self.id, self.proc_steps, self.time_limit_of_completion, self.properties)
        return infos


class ProductCC0(Product):
    def __init__(self, env, id, counter, properties):
        super().__init__(env, id, counter, properties)
        self.stations_location = {"base": None,
                                  "cap": None,
                                  "del": None
                                  }
        self.events = {"update_location": Event(self.env),
                       "new_location": Event(self.env, False),
                       "base": Event(self.env, False),  # events for location change
                       "cap": Event(self.env, False),
                       "del": Event(self.env, False),
                       "proc_base": Event(self.env, False),  # events for process steps
                       "proc_cap": Event(self.env, False),
                       "proc_del": Event(self.env, False),
                       "proc_completed": Event(self.env, False),
                       }

    def update_location(self):
        """update location"""
        yield self.events["base"].event & self.events["cap"].event
        self.current_location = self.stations_location["base"]
        self.next_destination_location = self.stations_location["cap"]
        self.events["new_location"].trigger()
        yield self.events["del"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["del"]
        self.events["new_location"].trigger()


class ProductCCX(Product):
    def __init__(self, env, id, counter, properties):
        super().__init__(env, id, counter, properties)
        self.stations_location = {"base": None,
                                  "ring": None,
                                  "cap": None,
                                  "del": None
                                  }
        self.events = {"update_location": Event(self.env),
                       "new_location": Event(self.env, False),
                       "base": Event(self.env, False),  # events for location change
                       "ring": Event(self.env, False),
                       "cap": Event(self.env, False),
                       "del": Event(self.env, False),
                       "proc_base": Event(self.env, False),  # events for process steps
                       "proc_ring": Event(self.env, False),
                       "proc_cap": Event(self.env, False),
                       "proc_del": Event(self.env, False),
                       "proc_completed": Event(self.env, False),
                       }

    def update_location(self):
        """update location"""
        yield self.events["base"].event & self.events["ring"].event
        self.current_location = self.stations_location["base"]
        self.next_destination_location = self.stations_location["ring"]
        self.events["new_location"].trigger()
        yield self.events["cap"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["cap"]
        self.events["new_location"].trigger()
        yield self.events["del"].event
        self.current_location = self.next_destination_location
        self.next_destination_location = self.stations_location["del"]
        self.events["new_location"].trigger()
