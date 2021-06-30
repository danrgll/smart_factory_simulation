# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import simpy
import random
from itertools import count

BASE_STATION_CAPACITY = 2  # number of base station
CAP_STATION_CAPACITY = 2  # number of cap station
RING_STATION_CAPACITY = 2  # number of ring station
STORAGE_CAPACITY = 1  # number of storage
DELIVERY_CAPACITY = 1  # number of delivery station
REPAIRMAN_CAPACITY = 1  # number of repairman
MOVER_CAPACITY = 1 # number of mover
"""
self.base_station = simpy.Resource(env, capacity=BASE_STATION_CAPACITY)
self.cap_station = simpy.Resource(env, capacity=CAP_STATION_CAPACITY)
self.ring_station = simpy.Resource(env, capacity=RING_STATION_CAPACITY)
self.storage = simpy.FilterStore(env, capacity=STORAGE_CAPACITY)
self.delivery = simpy.Resource(env, capacity=DELIVERY_CAPACITY)
self.repairman = simpy.Resource(env, capacity=REPAIRMAN_CAPACITY)
"""


class BaseStation(object):

    def __init__(self, env):
        self.env = env
        self.broken = False
        self.pt_mean = 2
        self.pt_sigma = .1
        self.mean_time_to_failure = 20
        self.repair_time = 10.0
        self.events = {
            "break": env.event(),  # machine breaks
            "part": env.event(),  # finished new part
        }
        self.input = False
        self.process = self.env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor())
        self.env.process(self.io())
        print("init base")

    def time_per_part(self):
        """Return actual processing time for a concrete part."""
        return random.normalvariate(1/  self.pt_mean, self.pt_sigma)

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        return random.expovariate(1/self.mean_time_to_failure)

    def io(self):
        print("Hier1")
        request = factory.base_station_resource.request()
        self.input = True
        print("input is True")
        yield request
        yield self.events.get("part")
        #wait for event
        factory.base_station_resource.release(request)
        self.input = False

    def monitor(self):
        """Monitor the production of parts."""
        print("start monitor")
        for part in count():
            yield self.events["part"]
            print("produced part #%i @t=%i" % (part, self.env.now))

    def working(self):
        """Produce parts as long as the simulation runs.

        While making a part, the machine may break several times.
        """
        print("start working")
        while True:
            #print(self.input)
            #if self.input is True:
                try:
                    yield self.env.timeout(self.time_per_part())
                    print("Timeout working")
                    self.events["part"].succeed()
                    self.events["part"] = self.env.event()
                except simpy.Interrupt:
                    self.broken = True
                    print("machine breaks @t=%i" % self.env.now)
                    yield self.env.timeout(self.repair_time)
                    print("machine running @t=%i" % self.env.now)
                    self.broken = False


    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                self.process.interrupt()


class Product(object):
    def __init__(self, base, ring, cap):
        self.base = base
        self.ring = ring
        self.cap = cap

    def process(self):
        print("process start")
        factory.base_stations_list[0].io()
        print("process io")




class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        self.env = simpy.Environment()
        self.base_station_resource = simpy.Resource(self.env, capacity=BASE_STATION_CAPACITY)
        self.base_stations_list = []
        #self.ring_stations_list = [None] * RING_STATION_CAPACITY
        #self.cap_stations_list = [None] * CAP_STATION_CAPACITY
        for i in range(0, BASE_STATION_CAPACITY):
            print("fac")
            self.base_stations_list.append(BaseStation(self.env))


        #self.base_station = BaseStation(self.env)
        #self.cap_station1 = CapStation(self.env)
        #self.cap_station2 = CapStation(self.env)
        #self.ring_station1 = RingStation(self.env)
        #self.ring_station2 = RingStation(self.env)
        #self.storage = Storage(self.env)
        #self.delivery = DeliveryStation(self.env)
        #self.repairman = Repairmen(self.env)


    def start_simulation(self):
        print("start_simluation")
        self.env.run()
        print("sim started")


"""
def c_0(env, factory, id):
    Steps to process product c_0.
    base_request = factory.base_station.request()
    yield base_request
    print('c_0  %d is at base station at %d ' % (id, env.now))
    processing_time = time_per_part()
    yield env.timeout(processing_time)
    factory.base_station.release(base_request)
    print('c_o %d is on the way to cap_station at %d ' % (id, env.now))
    trip_duration = 2
    yield env.timeout(trip_duration)
    cap_request = factory.cap_station.request()
    yield cap_request
    print('c_0  %d is at cap station at %d ' % (id, env.now))
    yield env.timeout(processing_time)
    factory.cap_station.release(cap_request)
    print('c_o %d is on the way to delivery station at %d ' % (id, env.now))
    yield env.timeout(trip_duration)
    del_request = factory.delivery.request()
    yield del_request
    print('c_0  %d is at delivery station at %d ' % (id, env.now))
    yield env.timeout(1)
    factory.delivery.release(del_request)
    print('c_0  %d is finished at %d ' % (id, env.now))
"""

if __name__ == '__main__':
    factory = Factory()
    #produce = Product(1, 1, 1)
    #produce.process()
    factory.start_simulation()
    print("Ende")


