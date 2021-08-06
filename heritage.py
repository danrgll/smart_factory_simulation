import random
import simpy
from simpy.events import AllOf, AnyOf


class Event(object):
    def __init__(self, env):
        self.env = env
        self.event = simpy.Event(self.env)

    def trigger(self, value=None):
        print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        self.event = simpy.Event(self.env)


class Process(object):
    def __init__(self, env, pt_mean, pt_sigma, pid, inputs=None, outputs=None, resources=None):
        self.env = env
        self.pt_mean = pt_mean
        self.pt_sigma = pt_sigma
        self.process_id = pid
        self.inputs = inputs
        if inputs is None:
            self.inputs = list()
        self.outputs = outputs
        if outputs is None:
            self.outputs = list()
        self.resources = resources
        if resources is None:
            self.resources = list()
        #self.env.process(self.running())

    def processing_time(self):
        """Returns actual processing time."""
        return max(0, random.normalvariate(self.pt_mean, self.pt_sigma))

    def running(self):
        while True:
            vals = yield AllOf(self.env, [x.event for x in self.inputs])
            yield self.env.timeout(self.processing_time())
            for o in self.outputs:
                o.trigger(value=self.process_id)


class MachineResource:
    def __init__(self, env, list_of_machines, capacity):
        self.env = env
        self.list_of_machines = list_of_machines
        self.resource = simpy.Resource(self.env, capacity)
        print("init MachineResourcwe")

    def request_release_resource(self):
        request = self.resource.request()
        yield request
        self.print_stats(self.resource)
        for machine in self.list_of_machines:
            if machine.ready is False and machine.broken is False:
                machine.ready = True
                yield self.env.process(machine.working())
                break
        self.resource.release(request)
        self.print_stats(self.resource)

    def print_stats(self,res):
        print(f'{res.count} of {res.capacity} slots are allocated.')
        #print(f'  Users: {res.users}')
        #print(f'  Queued events: {res.queue}')

