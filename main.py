# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import simpy




def car(env,id ,  driver):
    request = driver.request()
    yield request
    print('Start parking at %d ' % env.now + str(id))
    parking_duration = 5
    yield env.timeout(parking_duration)
    print('Start driving at %d ' % env.now + str(id))
    trip_duration = 2
    yield env.timeout(trip_duration)
    yield env.timeout(1)
    driver.release(request)



if __name__ == '__main__':
    env = simpy.Environment()
    driver = simpy.Resource(env, capacity=2)
    env.process(car(env, 1, driver))
    env.process(car(env, 2, driver))
    env.process(car(env, 3, driver))
    env.process(car(env, 4, driver))



    env.run(until=15)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
