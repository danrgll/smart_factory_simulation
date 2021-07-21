import random
from itertools import count
import simpy


class Event(object):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.event = simpy.Event(self.env)

    def trigger(self, value=None):
        print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        self.event = simpy.Event(self.env)


class Process(object):
    def __init__(self, env, pt_mean, pt_sigma, pid, ptype):
        self.env = env
        self.pt_mean = pt_mean
        self.pt_sigma = pt_sigma
        self.process_id = pid
        self.process_type = ptype

    def processing_time(self):
        """Returns actual processing time."""
        return max(0, random.normalvariate(self.pt_mean, self.pt_sigma))


class Machine(object):
    """Machines that process something"""
    def __init__(self, env: simpy.Environment, machine_id, repair_time: float, time_to_change_proc_type,
                 mean_time_to_failure: float, man_proc: dict):
        self.env = env
        self.machine_id = machine_id
        self.current_process = Process(self.env, 1, 0.1, 1, None)  # init process
        self.input = False
        self.broken = False
        self.mean_time_to_failure = mean_time_to_failure
        self.repair_time = repair_time
        self.man_proc = man_proc  # Manufacturing processes
        self.current_proc_type = None
        self.time_to_change_proc_type = time_to_change_proc_type
        self.events = {
            "break": Event(self.env),  # machine breaks
            "process_completed": Event(self.env),  # machine completed the process
        }
        self.data = []  # monitor processes
        self.process = env.process(self.working(self.current_process))
        self.env.process(self.break_machine())
        self.env.process(self.monitor(self.machine_id))

    def current_manufacturing_process_type(self, proc: Process):
        self.current_proc_type = proc.process_type
        yield self.env.timeout(3)  # time to change machine config to process new process type

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        fail_at = random.expovariate(self.mean_time_to_failure)
        print(f"machine {self.machine_id} will fail at {fail_at}")
        return fail_at

    def working(self, process: Process):
        """Processes pending processes

        While finish a process, the machine may break several times.
        """
        print("start working")
        # ToDo: prozess klasse einbauen und type Wechsel berücksichtigen
        # ToDo: Überprüfen on nach interupt der Prozess trotzdem noch abgearbeitet wird
        # ToDo: Gedanken über Events machen/Running funktion sinnvoll?
        # ToDo: Weil wir nicht interrupted vermutlich

        self.current_process = process
        # if self.current_process.process_type is not self.current_proc_type:
        #    self.env.timeout(self.time_to_change_proc_type)
        try:
            yield self.env.timeout(process.processing_time())
            self.events["process_completed"].trigger()
        except simpy.Interrupt:
            self.broken = True
            print(f"machine {self.machine_id} breaks @t={self.env.now}")
            yield self.env.timeout(self.repair_time)
            print(f"machine {self.machine_id} ready again @t={self.env.now}")
            self.broken = False

    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                try:
                    self.process.interrupt()
                except RuntimeError:
                    print(f"RunTimeError")
                    self.broken = True
                    print(f"machine {self.machine_id} breaks @t={self.env.now}")
                    yield self.env.timeout(self.repair_time)
                    print(f"machine {self.machine_id} running @t={self.env.now}")
                    self.broken = False

    def monitor(self, machine_id):
        """Monitor processes."""
        print("start monitor")
        for process in count():
            yield self.events["process_completed"].event
            item = (
                machine_id,
                process,
                self.env.now,
                self.current_process.process_id
            )
            self.data.append(item)
            print(f"machine {machine_id} completed process {process} @t={self.env.now}")


class MachineResource:
    """manages a amount of produced machines as a resource"""
    def __init__(self, env: simpy.Environment, machines: list, capacity: int, machine_type: str):
        self.env = env
        self.machines = machines
        self.resource = simpy.Resource(self.env, capacity)
        self.machine_type = machine_type
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

    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at {self.machine_type}.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')
