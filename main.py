# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import simpy
import random

PT_MEAN = 10            # average processing time
PT_SIGMA = 2            # sigma of processing time
MTTF = 300              # mean time to failure
BREAK_MEAN = 1 / MTTF   # parameter for expovariate distribution


def time_per_part():
    """Return actual processing time for a concrete part."""
    return random.normalvariate(PT_MEAN, PT_SIGMA)

def time_to_failure():
    """Return time until next failure for a machine."""
    return random.expovariate(BREAK_MEAN)


def c_0(env, base_res, cap_res, del_res, id ):
    base_request = base_res.request()
    yield base_request
    print('c_0  %d is at base station at %d ' % (id, env.now))
    processing_time = 4
    yield env.timeout(processing_time)
    base_res.release(base_request)
    print('c_o %d is on the way to cap_station at %d ' % (id, env.now))
    trip_duration = 2
    yield env.timeout(trip_duration)
    cap_request = cap_res.request()
    yield cap_request
    print('c_0  %d is at cap station at %d ' % (id, env.now))
    yield env.timeout(processing_time)
    cap_res.release(cap_request)
    print('c_o %d is on the way to delivery station at %d ' % (id, env.now))
    yield env.timeout(trip_duration)
    del_request = del_res.request()
    yield del_request
    print('c_0  %d is at delivery station at %d ' % (id, env.now))
    yield env.timeout(1)
    del_res.release(del_request)
    print('c_0  %d is finished at %d ' % (id, env.now))





if __name__ == '__main__':
    env = simpy.Environment()
    base_station = simpy.Resource(env, capacity=1)
    cap_station = simpy.Resource(env, capacity=2)
    ring_station = simpy.Resource(env, capacity=2)
    storage = simpy.FilterStore(env, capacity=1)
    delivery = simpy.Resource(env, capacity=1)
    repairman = simpy.Resource(env,capacity=1)
    env.process(c_0(env, base_station, cap_station, delivery, 1))
    env.process(c_0(env, base_station, cap_station, delivery, 2))
    env.process(c_0(env, base_station, cap_station, delivery, 3))
    env.process(c_0(env, base_station, cap_station, delivery, 4))

    env.run(until=30)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
