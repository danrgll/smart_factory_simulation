import random
import simpy
from itertools import count
import simpy
from simpy.events import AllOf, AnyOf


class Event(object):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.event = simpy.Event(self.env)

    def trigger(self, value=None):
        print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        self.event = simpy.Event(self.env)


class Process(object):
    def __init__(self, env, pt_mean, pt_sigma, pid, ptype,  inputs=None, outputs=None, resources=None):
        self.env = env
        self.pt_mean = pt_mean
        self.pt_sigma = pt_sigma
        self.process_id = pid
        self.process_type = ptype
        self.inputs = inputs
        if inputs is None:
            self.inputs = list()
        self.outputs = outputs
        if outputs is None:
            self.outputs = list()
        self.resources = resources
        if resources is None:
            self.resources = list()
        self.proc = self.env.process(self.running())

    def processing_time(self):
        """Returns actual processing time."""
        return max(0, random.normalvariate(self.pt_mean, self.pt_sigma))

    def running(self):
        yield AllOf(self.env, [x.event for x in self.inputs])
        yield self.env.timeout(self.processing_time())
        for o in self.outputs:
            o.trigger(value=self.process_id)


class Machine(object):
    def __init__(self, env: simpy.Environment, machine_id, repair_time: float, time_to_change_proc_type,
                 mean_time_to_failure: float, man_proc: dict):
        self.env = env
        self.machine_id = machine_id
        self.current_process = None
        self.input = False
        self.broken = False
        self.mean_time_to_failure = mean_time_to_failure
        self.repair_time = repair_time
        self.man_proc = man_proc  # Manufacturing processes
        self.current_proc_type = None
        self.time_to_change_proc_type = time_to_change_proc_type
        self.events = {
            "break": env.event(),  # machine breaks
            "process_completed": env.event(),  # machine completed the process
        }
        self.process = env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor(self.machine_id))

    def current_manufacturing_process_type(self, proc: Process):
        self.current_proc_type = proc.process_type
        self.env.timeout(3)  # time to change machine config to process new process type

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        return random.expovariate(1 / self.mean_time_to_failure)

    def working(self, process):
        """Processes pending processes

        While finish a process, the machine may break several times.
        """
        print("start working")
        # ToDo: prozess klasse einbauen und type Wechsel berücksichtigen
        # ToDo: Überprüfen on nach interupt der Prozess trotzdem noch abgearbeitet wird
        # ToDo: Gedanken über Events machen/Running funktion sinnvoll?
        # ToDo: Weil wir nicht interrupted vermutlich

        #self.current_process = process
        #if self.current_process.process_type is not self.current_proc_type:
        #    self.env.timeout(self.time_to_change_proc_type)
        try:
            #test
            proc = self.env.process(self.current_process.running())
            yield proc
            #test ende
            self.events["process_completed"].succeed()
            self.events["process_completed"] = self.env.event()
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

    def monitor(self, machine_id):
        """Monitor the production of parts."""
        print("start monitor")
        for process in count():
            yield self.events["process_completed"]
            print(f"machine {machine_id} completed process {process} @t={self.env.now}")


class MachineResource:
    def __init__(self, env: simpy.Environment, machines: list, capacity: int):
        self.env = env
        self.machines = machines
        self.resource = simpy.Resource(self.env, capacity)
        print("init MachineResource")

    def request_release_resource(self, process):
        request = self.resource.request()
        yield request
        self.print_stats(self.resource)
        for machine in self.machines:
            if machine.input is False and machine.broken is False:
                machine.input = True
                yield self.env.process(machine.working(process))
                break
        self.resource.release(request)
        self.print_stats(self.resource)

    def print_stats(self,res):
        print(f'{res.count} of {res.capacity} slots are allocated.')
        #print(f'  Users: {res.users}')
        #print(f'  Queued events: {res.queue}')