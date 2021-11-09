import simpy
from simpy import AllOf
import random


class Event(object):
    def __init__(self, env: simpy.Environment, reuse=True):
        self.env = env
        self.reuse = reuse
        self.event = simpy.Event(self.env)

    def trigger(self, value=None):
        """trigger self.event and if we want to use this event again create a new simpy.Event"""
        self.event.succeed(value=value)
        if self.reuse is True:
            self.event = simpy.Event(self.env)


class Process(object):
    """A process controls the production step of a product. As a prerequisite for the start of the production step,
     so-called input events can be present, which must be waited for. After occurrence, the process requests the
      resources required for the production step. After receiving all resources, the process signals that the
       processing of the production step can be started. After completion of the production step, the process triggers
        its associated output events.
"""
    def __init__(self, env, product, pid, inputs=None, outputs=None, resources=None, priority=10):
        self.env = env
        self.process_id = pid
        self.product = product
        self.priority = priority
        # input events for which the process is waiting
        self.inputs = inputs
        if inputs is None:
            self.inputs = list()
        # output events which the process triggerd after completion
        self.outputs = outputs
        if outputs is None:
            self.outputs = list()
        self.resources = resources
        if resources is None:
            self.resources = list()
        self.get_events = list()  # Events that mark if the resources are accessible which are required for the process
        self.process_steps_events = list()
        self.got_all_resources = False
        self.process = self.env.process(self.check_input_events())
        self.process_running = None

    def check_input_events(self):
        """Checks whether all assumed events have occurred. When the events have occurred. The required resources
        of the process are requested and the process execution is started."""
        yield AllOf(self.env, [x.event for x in self.inputs])
        self.get_resources()
        self.process_running = self.env.process(self.running())

    def get_resources(self):
        """calls for required resources with the given priority"""
        start_next_proc_step_yield = Event(self.env, False)
        start_next_proc_step_trigger = Event(self.env, False)
        self.process_steps_events.append(start_next_proc_step_yield)
        for resource in self.resources:
            self.process_steps_events.append(start_next_proc_step_trigger)
            get_event = Event(self.env, False)
            release_event = Event(self.env)
            self.get_events.append(get_event)
            # Requests the individual resources
            self.env.process(resource.request_release_resource(get_event, release_event, start_next_proc_step_yield,
                                                               start_next_proc_step_trigger, self.process_id,
                                                               self.product, self.priority))
            start_next_proc_step_yield = start_next_proc_step_trigger
            start_next_proc_step_trigger = Event(self.env, False)

    def running(self):
        """starts the execution of the actual process and triggers all output events after its execution."""
        proc_completed = False
        while proc_completed is False:
            try:
                yield AllOf(self.env, [x.event for x in self.get_events])
                self.got_all_resources = True
                self.product.events["update_location"].trigger()  # update location of product event
                self.product.monitor.monitor("TRIGGER", self.env.now, self.resources)
                self.process_steps_events.pop(0).trigger()  # trigger event to start first process step
                yield AllOf(self.env, [x.event for x in self.process_steps_events])
                for o in self.outputs:
                    o.trigger(value=self.process_id)
                proc_completed = True
            except simpy.Interrupt:
                pass


class Resource(object):
    """A resource that self-manages requests and allocations to them"""
    def __init__(self, env: simpy.Environment, resource_type, location, capacity: int, processing_time):
        self.env = env
        self.location = location
        self.resource = simpy.PreemptiveResource(self.env, capacity)
        self.resource_type = resource_type
        self.processing_time_settings = processing_time  # (pt_mean, pt_sigma)
        self.current_processes = []
        self.number_of_current_proc = 0
        self.interrupted = []

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event,
                                 start_next_proc_step_trigger: Event, proc_id, product, priority):
        """request and hold resource. After event is triggered release resource"""
        completed = False
        event_suceed = Event(self.env, False)
        while completed is False:
            n = False
            product.monitor.monitor("ASK", self.env.now, self.resource_type)
            flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                try:
                    i = True
                    yield req
                    i = False
                    if flag is True:
                        if len(self.interrupted) != 0:
                            infos = self.interrupted.pop(0)
                            # [[currently_using, product, proc_id, pointer]
                            if infos[3] is not None:
                                pointer = infos[3]
                            else:
                                pointer = infos
                            # pointer = [current_event, proc, prod, request]
                            currently_using = Event(self.env, False)
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                        else:
                            currently_using = Event(self.env, False)
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                        product.monitor.monitor("BEKOMMT", self.env.now, self.resource_type)
                    t = True
                    if pointer is not None:
                        # [[currently_using, product, proc_id, pointer]
                        if pointer[1].processes[pointer[2]].got_all_resources is True and pointer[0].event.triggered \
                                is False:
                            product.monitor.monitor("PROZESS DER BÖSE", self.env.now, self.resource_type)
                            yield pointer[0].event
                            t = False
                        elif flag is True:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                    if t is True:
                        n = True
                        slot = self.env.process(self.request_slot(get_resource, release_resource,
                                                                  start_next_proc_step_yield,
                                                                  start_next_proc_step_trigger, proc_id,
                                                                  product, event_suceed))
                        yield release_resource.event
                        completed = True
                        n = False
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                        currently_using.trigger()
                except simpy.Interrupt:
                    if i is False:
                        self.interrupted.append([currently_using, product, proc_id, pointer])
                        if [priority, product, proc_id, currently_using] in self.current_processes:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                        product.monitor.monitor("UNTERBROCHEN", self.env.now, self.resource_type)
                        if t is True and n is True and product.processes[proc_id].got_all_resources is False:
                            product.processes[proc_id].get_events.remove(get_resource)
                            get_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.append(get_resource)
                            product.processes[proc_id].process_running.interrupt()
                            slot.interrupt()
                        elif product.processes[proc_id].got_all_resources is True:
                            yield event_suceed.event
                            completed = True
                            currently_using.trigger()
                        else:
                            currently_using.trigger()

    def request_slot(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event,
                     start_next_proc_step_trigger: Event, proc_id, product, event_succed):
        """request a resource slot"""
        try:
            c = self.env.process(self.send_location_to_product(product))
            get_resource.trigger()  # event to signal that you get the resource
            yield start_next_proc_step_yield.event  # wait for resource which are in the production step before
            self.env.process(self.process_slot(product, start_next_proc_step_trigger, release_resource, event_succed))
        except simpy.Interrupt:
            c.interrupt()  # while waiting, the request can be interrupted for priority reasons

    def process_slot(self, product, start_next_proc_step_trigger, release_resource, event_suceed):
        """simulates the use of the resource by a process. After use, the resource object is signaled to release the
        slot again and the next resource of the production step is signaled to start with its part."""
        yield self.env.timeout(self.processing_time())
        product.monitor.monitor("WURDE FERTIGGESTELLT", self.env.now, self.resource_type)
        event_suceed.trigger()
        start_next_proc_step_trigger.trigger()  # signal für next resource to start
        release_resource.trigger()

    def processing_time(self):
        """Time needed by the process to complete the production step at the resource."""
        return round(abs(random.normalvariate(self.processing_time_settings[0], self.processing_time_settings[1])))

    def send_location_to_product(self, product):
        """passes the location of the resource to the product. This information is needed later for the transport."""
        try:
            yield product.events["update_location"].event
            product.stations_location[self.resource_type] = self.location
            product.events[self.resource_type].trigger()
        except simpy.Interrupt:
            return


class MachineResource(object):
    """manages a amount of produced machines as a resource"""
    def __init__(self, env: simpy.Environment, machines: list, machine_type: str):
        self.env = env
        self.machines = machines
        self.resource = simpy.PreemptiveResource(self.env, capacity=len(self.machines))
        self.resource_type = "machine"
        self.machine_type = machine_type
        self.current_processes = []
        self.number_of_current_proc = 0
        self.interrupted = []
        for machine in self.machines:
            machine.resource = self.resource

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event,
                                 start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        """request and hold resource. Assigns a machine to the requesting process. If the resource capacity is full
        and a higher priority process requests, the allocation can be interrupted and the request rejoins
        the manager's queue. After event is triggered release resource. """
        completed = False
        machine_process_succeed = Event(self.env, False)
        new_try = Event(self.env)
        n = False
        while completed is False:
            product.monitor.monitor("ASK", self.env.now, self.machine_type)
            flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                try:
                    i = True
                    yield req
                    i = False
                    if flag is True:
                        if len(self.interrupted) != 0:
                            infos = self.interrupted.pop(0)
                            # [[currently_using, product, proc_id, pointer]
                            if infos[3] is not None:
                                pointer = infos[3]
                                # print("pointer not None")
                            else:
                                pointer = infos
                            # pointer = [current_event, proc, prod, request]
                            currently_using = Event(self.env, False)
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                        else:
                            currently_using = Event(self.env, False)
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                    product.monitor.monitor("BEKOMMT", self.env.now, self.machine_type)
                    t = True
                    if pointer is not None:
                        # [[currently_using, product, proc_id, pointer]
                        if pointer[1].processes[pointer[2]].got_all_resources is True and pointer[0].event.triggered \
                                is False:
                            product.monitor.monitor("PROZESS DER BÖSE", self.env.now, self.machine_type)
                            yield pointer[0].event
                            t = False
                            currently_using.trigger()
                        elif flag is True:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                    if t is True:
                        n = True
                        get_machine = False
                        while get_machine is False:
                            for machine in self.machines:
                                if machine.in_progress is False and machine.broken is False:
                                    machine.in_progress = True
                                    c = machine
                                    machine.input_process = self.env.process(machine.input(proc_id, get_resource,
                                                                                           release_resource,
                                                                                           start_next_proc_step_yield,
                                                                                           start_next_proc_step_trigger,
                                                                                           product,
                                                                                           machine_process_succeed,
                                                                                           new_try))
                                    get_machine = True
                                    break
                        yield release_resource.event
                        if machine_process_succeed.event.triggered is True:
                            completed = True
                        else:
                            release_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.remove(get_resource)
                            get_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.append(get_resource)
                            product.processes[proc_id].process_running.interrupt()
                        n = False
                        currently_using.trigger()
                    if [priority, product, proc_id, currently_using, pointer, req] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                except simpy.Interrupt:
                    if i is False:
                        self.interrupted.append([currently_using, product, proc_id, pointer])
                        if [priority, product, proc_id, currently_using, pointer, req] in self.current_processes:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                        if product.processes[proc_id].got_all_resources is False and n is True:
                            product.processes[proc_id].get_events.remove(get_resource)
                            get_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.append(get_resource)
                            product.processes[proc_id].process_running.interrupt()
                            c.input_process.interrupt()
                            yield new_try.event
                            currently_using.trigger()
                        elif product.processes[proc_id].got_all_resources is True:
                            yield machine_process_succeed.event
                            completed = True
                            n = False
                            currently_using.trigger()


class MoverResource(object):
    """manages a amount of movers as a resource"""
    def __init__(self, env: simpy.Environment, movers: list):
        self.env = env
        self.movers = movers
        self.resource = simpy.PreemptiveResource(self.env, capacity=len(self.movers))
        self.current_processes = []
        self.number_of_current_proc = 0
        self.resource_type = "mover"
        self.interrupted = []

    def request_release_resource(self, get_resource: Event, release_resource: Event,
                                 start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        """Request, hold and release resource. Assigns movers to the processes. Can be interrupted when processes
        with a higher priority request."""
        work_done = False
        machine_process_succeed = Event(self.env, False)
        new_try = Event(self.env)
        n = False
        while work_done is False:
            product.monitor.monitor("ASK", self.env.now, "mover")
            flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                try:
                    i = True
                    yield req
                    i = False
                    if flag is True:
                        if len(self.interrupted) != 0:
                            infos = self.interrupted.pop(0)
                            # [[currently_using, product, proc_id, pointer]
                            if infos[3] is not None:
                                pointer = infos[3]
                            else:
                                pointer = infos
                            # pointer = [current_event, proc, prod, request]
                            currently_using = Event(self.env, False)
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                        else:
                            currently_using = Event(self.env, False)
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                    product.monitor.monitor("BEKOMMT", self.env.now, self.resource_type)
                    t = True
                    if pointer is not None:
                        # [[currently_using, product, proc_id, pointer]
                        if pointer[1].processes[pointer[2]].got_all_resources is True and pointer[0].event.triggered \
                                is False:
                            product.monitor.monitor("PROZESS DER BÖSE", self.env.now, self.resource_type)
                            yield pointer[0].event
                            t = False
                            currently_using.trigger()
                        elif flag is True:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                            pointer = None
                            self.current_processes.append([priority, product, proc_id, currently_using, pointer, req])
                    if t is True:
                        n = True
                        get_machine = False
                        while get_machine is False:
                            for mover in self.movers:
                                if mover.reserved is False:
                                    mover.reserved = True
                                    c = self.env.process(
                                        mover.transport_update(proc_id, product, get_resource, release_resource,
                                                               start_next_proc_step_yield,
                                                               start_next_proc_step_trigger, new_try,
                                                               machine_process_succeed))
                                    get_machine = True
                                    break
                        yield release_resource.event
                        work_done = True
                        n = False
                        currently_using.trigger()
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                except simpy.Interrupt:
                    if i is False:
                        self.interrupted.append([currently_using, product, proc_id, pointer])
                        if [priority, product, proc_id, currently_using] in self.current_processes:
                            self.current_processes.remove([priority, product, proc_id, currently_using, pointer, req])
                        if product.processes[proc_id].got_all_resources is False and n is True:
                            product.processes[proc_id].get_events.remove(get_resource)
                            get_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.append(get_resource)
                            product.processes[proc_id].process_running.interrupt()
                            c.interrupt()
                            yield new_try.event
                            currently_using.trigger()
                        elif product.processes[proc_id].got_all_resources is True:
                            yield machine_process_succeed.event
                            work_done = True
                            n = False
                            currently_using.trigger()


class RepairmenResource(object):
    """manages a amount of movers as a resource"""
    def __init__(self, env, repairmen: list):
        self.env = env
        self.repairmen = repairmen
        self.resource = simpy.PriorityResource(self.env, capacity=len(repairmen))

    def request_release_resource(self, job_location, wait_until_repaired: Event):
        """Request, hold and release resource. Assigns repairman to the requesting machine. The resource is
        released again after the malfunction on the machine has been eliminated. """
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
