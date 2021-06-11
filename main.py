# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import simpy
import random

BASE_STATION_CAPACITY = 1        # number of base station
CAP_STATION_CAPACITY = 2         # number of cap station
RING_STATION_CAPACITY = 2        # number of ring station
STORAGE_CAPACITY = 1             # number of storage
DELIVERY_CAPACITY = 1            # number of delivery station
REPAIRMAN_CAPACITY = 1           # number of repairman
PT_MEAN = 10                     # average processing time
PT_SIGMA = 2                     # sigma of processing time
MTTF = 300                       # mean time to failure
BREAK_MEAN = 1 / MTTF            # parameter for expovariate distribution


class Factory:
    """create amount of resources(machines)"""
    def __init__(self, env):
        self.base_station = simpy.Resource(env, capacity=BASE_STATION_CAPACITY)
        self.cap_station = simpy.Resource(env, capacity=CAP_STATION_CAPACITY)
        self.ring_station = simpy.Resource(env, capacity=RING_STATION_CAPACITY)
        self.storage = simpy.FilterStore(env, capacity=STORAGE_CAPACITY)
        self.delivery = simpy.Resource(env, capacity=DELIVERY_CAPACITY)
        self.repairman = simpy.Resource(env, capacity=REPAIRMAN_CAPACITY)


def time_per_part():
    """Return actual processing time for a concrete part."""
    return random.normalvariate(PT_MEAN, PT_SIGMA)


def time_to_failure():
    """Return time until next failure for a machine."""
    return random.expovariate(BREAK_MEAN)


def c_0(env, factory, id):
    """ Steps to process product c_0."""
    base_request = factory.base_station.request()
    yield base_request
    print('c_0  %d is at base station at %d ' % (id, env.now))
    processing_time = 4
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


if __name__ == '__main__':
    env = simpy.Environment()
    factory = Factory(env)
    env.process(c_0(env, factory, 1))
    env.process(c_0(env, factory, 2))
    env.process(c_0(env, factory, 3))
    env.process(c_0(env, factory, 4))
    env.run(until=30)


