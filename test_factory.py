import heritage
import simpy
import random
from itertools import count


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
        self.process = env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor())
        print("init base")

    def time_per_part(self):
        """Return actual processing time for a concrete part."""
        return random.normalvariate(1/self.pt_mean, self.pt_sigma)

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        return random.expovariate(1/self.mean_time_to_failure)


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
        try:
            yield self.env.timeout(self.time_per_part())
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
                try:
                    self.process.interrupt()
                except RuntimeError:
                    self.broken = True
                    print("machine breaks @t=%i" % self.env.now)
                    yield self.env.timeout(self.repair_time)
                    print("machine running @t=%i" % self.env.now)
                    self.broken = False


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        self.env = simpy.Environment()
        self.base1 = BaseStation(self.env)
        self.base2 = BaseStation(self.env)
        self.machine_resource = heritage.MachineResource(self.env, [self.base1, self.base2], 2)
        self.env.process(self.product(1))
        self.env.process(self.product(2))
        self.env.process(self.product(3))
        self.env.process(self.product(4))

    def start_simulation(self):
        print("start_simluation")
        self.env.run(until=100)
        print("sim started")

    def product(self, id):
        base_process = self.env.process(self.machine_resource.request_release_resource())
        yield base_process
        print(f"product {id} has been completed")

if __name__ == '__main__':
    factory = Factory()
    factory.start_simulation()
    print("Ende")