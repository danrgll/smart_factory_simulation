import simpy
import tester
from simpy import AllOf
import random


class Event(object):
    def __init__(self, env: simpy.Environment, reuse=True):
        self.env = env
        self.reuse = reuse
        self.event = simpy.Event(self.env)


    def trigger(self, value=None):
        """trigger self.event and if we want to use this event again create a new simpy.Event"""
        # print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        if self.reuse is True:
            self.event = simpy.Event(self.env)


class Process(object):
    # ToDo: schauen welche Events wir nochmal benötigen. Falls nicht reuse=False setzen
    def __init__(self, env, product, pid, inputs=None, outputs=None, resources=None, priority=10):
        self.env = env
        self.process_id = pid
        self.product = product
        self.priority = priority
        self.inputs = inputs
        if inputs is None:
            self.inputs = list()
        self.outputs = outputs
        if outputs is None:
            self.outputs = list()
        self.resources = resources
        if resources is None:
            self.resources = list()
        self.get_events = list()  # Events that mark if the resources are accessible which are required for the process
        self.process_steps_events = list()
        self.process = self.env.process(self.check_input_events())

    def check_input_events(self):
        # checken ob Reihenfolge beibehalten wird
        yield AllOf(self.env, [x.event for x in self.inputs])
        self.get_resources()
        self.env.process(self.running())

    def get_resources(self):
        """calls for required resources"""
        # Lösung der Resourcen reihenfolge anfragen. So in liste geben wie man es auch gerne nutzen würde.
        #init_process = Event(self.env)  # wait until all inquiries have been initialized
        start_next_proc_step_yield = Event(self.env, False)
        start_next_proc_step_trigger = Event(self.env, False)
        self.process_steps_events.append(start_next_proc_step_yield)
        for resource in self.resources:
            self.process_steps_events.append(start_next_proc_step_trigger)
            get_event = Event(self.env)
            release_event = Event(self.env)
            self.get_events.append(get_event)
            tester.d.__next__()
            # resource machine
            self.env.process(resource.request_release_resource(get_event, release_event, start_next_proc_step_yield, start_next_proc_step_trigger, self.process_id, self.product, self.priority))
            start_next_proc_step_yield = start_next_proc_step_trigger
            start_next_proc_step_trigger = Event(self.env, False)
        #self.env.process(self.running(init_process))


    def running(self):
        # ToDo: Hier werden die einzelnen Resourcen abgearbeotet und wieder freigegeben am Ende wird das Output event getriggerd
        #init_process.trigger()
        yield AllOf(self.env, [x.event for x in self.get_events])
        self.process_steps_events.pop(0).trigger()  # trigger event to start first process step
        yield AllOf(self.env, [x.event for x in self.process_steps_events])
        for o in self.outputs:
            o.trigger(value=self.process_id)


class Resource(object):
    def __init__(self, env: simpy.Environment, resource_type, location, capacity: int, processing_time):
        self.env = env
        self.location = location
        self.resource = simpy.PriorityResource(self.env, capacity)
        self.resource_type = resource_type
        self.processing_time_settings = processing_time #  (pt_mean, pt_sigma)

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event, proc_id, product, priority):
        # ToDo: wo wird event getriggered?? in Klasse Proccesses als Output gute Möglichkeit
        """request and hold resource. After event is triggered release resource"""
        #yield init_process.event
        request = self.resource.request(priority)
        yield request
        product.stations_location[self.resource_type] = self.location
        product.events[self.resource_type].trigger()
        get_resource.trigger()  # event to signal that you get the resource
        # ToDo yield event was Prozess startet. gesteuert über Product.
        yield start_next_proc_step_yield.event
        yield self.env.timeout(self.processing_time())
        product.monitor.monitor_event.trigger()  # monitor that you are done with production
        start_next_proc_step_trigger.trigger()
        # yield release_resource.event # keine Verwendung hier
        self.resource.release(request)

    def processing_time(self):
        return abs(random.normalvariate(self.processing_time_settings[0], self.processing_time_settings[1]))


class MachineResource(object):
    """manages a amount of produced machines as a resource"""
    def __init__(self, env: simpy.Environment, machines: list, machine_type: str):
        self.env = env
        self.machines = machines
        self.resource = simpy.PriorityResource(self.env, capacity=len(self.machines))
        self.resource_type = "machine"
        self.machine_type = machine_type
        for machine in self.machines:
            machine.resource = self.resource

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        #yield init_process.event
        request = self.resource.request(priority)
        tester.e.__next__()
        yield request
        tester.a.__next__()
        get_machine = False
        while get_machine is False:
            for machine in self.machines:
                if machine.in_progress is False and machine.broken is False:
                    tester.c.__next__()
                    machine.in_progress = True
                    self.env.process(machine.input(proc_id,get_resource, release_resource, start_next_proc_step_yield, start_next_proc_step_trigger, product))  # übergebe process an maschine
                    get_machine = True
                    break
        yield release_resource.event
        tester.j.__next__()
        self.resource.release(request)
    """
    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at {self.machine_type}.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')
    """

class MoverResource(object):
    def __init__(self, env: simpy.Environment, movers: list):
        self.env = env
        self.movers = movers
        self.resource = simpy.PriorityResource(self.env,capacity=len(self.movers))
        #ToDO: benötige ich ier überhaupt Resource_type
        self.resource_type = "mover"
    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        #yield init_process.event
        request = self.resource.request(priority)
        yield request
        for mover in self.movers:
            if mover.reserved is False:
                mover.reserved = True
                self.env.process(mover.transport_update(product, get_resource, release_resource, start_next_proc_step_yield, start_next_proc_step_trigger))
                break
        yield release_resource.event
        self.resource.release(request)


    """
    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at mover.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')
    """

class RepairmenResource(object):
    def __init__(self, env, repairmen: list):
        self.env = env
        self.repairmen = repairmen
        self.resource = simpy.PriorityResource(self.env, capacity=len(repairmen))

    def request_release_resource(self, job_location, wait_until_repaired: Event):
        request = self.resource.request()
        release_resource = Event(self.env)
        yield request
        for repairman in self.repairmen:
            if repairman.busy is False:
                repairman.busy = True
                self.env.process(repairman.work(job_location, release_resource))
                break
        yield release_resource.event
        self.resource.release(request)
        wait_until_repaired.trigger()









