class RingStation(object):

    def __init__(self, env):
        self.env = env
        self.broken = False
        self.pt_mean = 60.0 / 100
        self.pt_sigma = .1
        self.mean_time_to_failure = 20
        self.repair_time = 10.0
        self.events = {
            "break": self.env.event(),  # machine breaks
            "part": self.env.event(),  # finished new part
        }
        self.process = self.env.process(self.working())
        print("test")
        self.env.process(self.break_machine())
        self.env.process(self.monitor())
        self.env.process(self.io())

    def time_per_part(self):
        """Return actual processing time for a concrete part."""
        return random.normalvariate(self.pt_mean, self.pt_sigma)

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        return random.expovariate(self.mean_time_to_failure)


    def working(self):
        """Produce parts as long as the simulation runs.

        While making a part, the machine may break several times.
        """
        while True:
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

    def monitor(self):
        """Monitor the production of parts."""
        for part in count():
            yield self.events["part"]
            print("produced part #%i @t=%i" % (part, self.env.now))


    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                self.process.interrupt()


class CapStation(object):

    def __init__(self, env):
        self.env = env
        self.broken = False
        self.pt_mean = 60.0 / 100
        self.pt_sigma = .1
        self.mean_time_to_failure = 20
        self.repair_time = 10.0
        self.events = {
            "break": self.env.event(),  # machine breaks
            "part": self.env.event(),  # finished new part
        }
        self.process = self.env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor())

    def time_per_part(self):
        """Return actual processing time for a concrete part."""
        return random.normalvariate(self.pt_mean, self.pt_sigma)

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        return random.expovariate(self.mean_time_to_failure)

    def working(self):
        """Produce parts as long as the simulation runs.

        While making a part, the machine may break several times.
        """
        while True:
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

    def monitor(self):
        """Monitor the production of parts."""
        for part in count():
            yield self.events["part"]
            print("produced part #%i @t=%i" % (part, self.env.now))

    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                self.process.interrupt()


class DeliveryStation(object):

    def __init__(self, env):
        self.env = env


class Storage(object):

    def __init__(self, env):
        self.env = env

class Mover(object):

    def __init__(self, env):
        self.env = env

class Repairmen(object):

    def __init__(self, env):
        self.env = env