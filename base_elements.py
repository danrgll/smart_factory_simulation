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
        self.got_all_resources = False
        self.process = self.env.process(self.check_input_events())
        self.process_running = None

    def check_input_events(self):
        # checken ob Reihenfolge beibehalten wird
        yield AllOf(self.env, [x.event for x in self.inputs])
        self.get_resources()
        self.process_running = self.env.process(self.running())

    def get_resources(self):
        """calls for required resources"""
        start_next_proc_step_yield = Event(self.env, False)
        start_next_proc_step_trigger = Event(self.env, False)
        self.process_steps_events.append(start_next_proc_step_yield)
        for resource in self.resources:
            self.process_steps_events.append(start_next_proc_step_trigger)
            get_event = Event(self.env, False)
            # ToDO: wo brauche ich den release Evebt
            release_event = Event(self.env)
            self.get_events.append(get_event)
            tester.d.__next__()
            # resource machine
            self.env.process(resource.request_release_resource(get_event, release_event, start_next_proc_step_yield, start_next_proc_step_trigger, self.process_id, self.product, self.priority))
            start_next_proc_step_yield = start_next_proc_step_trigger
            start_next_proc_step_trigger = Event(self.env, False)


    def running(self):
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
                return


class Resource(object):
    def __init__(self, env: simpy.Environment, resource_type, location, capacity: int, processing_time):
        self.env = env
        self.location = location
        self.resource = simpy.PreemptiveResource(self.env, capacity)
        self.resource_type = resource_type
        self.processing_time_settings = processing_time #  (pt_mean, pt_sigma)
        self.current_processes = []
        self.number_of_current_proc = 0

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event, proc_id, product, priority):
        """request and hold resource. After event is triggered release resource"""
        completed = False
        while completed is False:
            flag = False
            product.monitor.monitor("ASK", self.env.now, self.resource_type)
            if len(self.current_processes) == self.resource.capacity:
                prio, prod, id, current_event = max(self.current_processes, key=lambda item: item[0])
                print(prio, prod, id, current_event)
                proc = prod.processes[id]
                if proc.got_all_resources is False and priority < prio:
                    self.current_processes.remove([prio, prod, id, current_event])
                    flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                yield req
                product.monitor.monitor("BEKOMMEN", self.env.now, self.resource_type)
                try:
                    t = True
                    if flag is True:
                        if proc.got_all_resources is True:
                            yield current_event.event
                            t = False
                        elif current_event.event.triggered is not True:
                            currently_using = Event(self.env, False)
                            self.current_processes.append([priority, product, proc_id, currently_using])
                            self.number_of_current_proc += 1
                        else:
                            currently_using = Event(self.env, False)
                            self.current_processes.append([priority, product, proc_id, currently_using])
                            self.number_of_current_proc += 1
                    else:
                        currently_using = Event(self.env, False)
                        self.current_processes.append([priority, product, proc_id, currently_using])
                        self.number_of_current_proc += 1
                    if t is True:
                        c = self.env.process(self.send_location_to_product(product))
                        get_resource.trigger()  # event to signal that you get the resource
                        yield start_next_proc_step_yield.event
                        yield self.env.timeout(self.processing_time())
                        product.monitor.monitor("WURDE FERTIGGESTELLT",self.env.now, self.resource_type)
                        start_next_proc_step_trigger.trigger()
                        completed = True
                        if [priority, product, proc_id, currently_using] in self.current_processes:
                            self.current_processes.remove([priority, product, proc_id, currently_using])
                            self.number_of_current_proc -= 1
                        currently_using.trigger()

                except simpy.Interrupt:
                    product.monitor.monitor("UNTERBROCHEN", self.env.now, self.resource_type)
                    product.processes[proc_id].get_events.remove(get_resource)
                    get_resource = Event(self.env, False)
                    product.processes[proc_id].get_events.append(get_resource)
                    product.processes[proc_id].process_running.interrupt()
                    c.interrupt()
                    currently_using.trigger()

    def send_location_to_product(self, product):
        try:
            yield product.events["update_location"].event
            product.stations_location[self.resource_type] = self.location
            product.events[self.resource_type].trigger()
        except simpy.Interrupt:
            return



    def processing_time(self):
        return abs(random.normalvariate(self.processing_time_settings[0], self.processing_time_settings[1]))


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
        for machine in self.machines:
            machine.resource = self.resource

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        completed = False
        machine_process_succeed = Event(self.env, False)
        new_try = Event(self.env)
        n = False
        while completed is False:
            product.monitor.monitor("ASK", self.env.now, self.machine_type)
            flag = False
            if len(self.current_processes) == self.resource.capacity:
                prio, prod, id, current_event = max(self.current_processes, key=lambda item: item[0])
                print(prio, prod, id, current_event)
                proc = prod.processes[id]
                if proc.got_all_resources is False and priority < prio:
                    self.current_processes.remove([prio,prod,id,current_event])
                    flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                yield req
                try:
                    product.monitor.monitor("BEKOMMT", self.env.now, self.machine_type)
                    t = True
                    currently_using = Event(self.env, False)
                    self.current_processes.append([priority, product, proc_id, currently_using])
                    self.number_of_current_proc += 1
                    if flag is True:
                        if proc.got_all_resources is True and current_event.event.triggered is False:
                            product.monitor.monitor("PROZESS DER BÖSE", self.env.now, self.machine_type)
                            yield current_event.event
                            t = False
                    if t is True:
                        n = True
                        get_machine = False
                        for machine in self.machines:
                            print(machine.machine_id, machine.in_progress, machine.broken)
                        while get_machine is False:
                            for machine in self.machines:
                                if machine.in_progress is False and machine.broken is False:
                                    tester.c.__next__()
                                    machine.in_progress = True
                                    print(f"{self.machine_type}get machine, {machine.machine_type, machine.machine_id, product.product_infos()}")
                                    machine.input_process = self.env.process(machine.input(proc_id,get_resource, release_resource, start_next_proc_step_yield, start_next_proc_step_trigger, product, machine_process_succeed, new_try))# übergebe process an maschine
                                    get_machine = True
                                    break
                        yield release_resource.event
                        if machine_process_succeed.event.triggered is True:
                            completed = True
                        else:
                            product.processes[proc_id].get_events.remove(get_resource)
                            get_resource = Event(self.env, False)
                            product.processes[proc_id].get_events.append(get_resource)
                            product.processes[proc_id].process_running.interrupt()
                        n = False
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using])
                        self.number_of_current_proc -= 1
                    currently_using.trigger()
                except simpy.Interrupt:
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using])
                        self.number_of_current_proc -= 1
                    if product.processes[proc_id].got_all_resources is False and n is True:
                        product.processes[proc_id].get_events.remove(get_resource)
                        get_resource = Event(self.env, False)
                        product.processes[proc_id].get_events.append(get_resource)
                        product.processes[proc_id].process_running.interrupt()
                        machine.input_process.interrupt()
                    elif product.processes[proc_id].got_all_resources is True:
                        yield machine_process_succeed.event
                        for machine in self.machines:
                            if machine.current_process == proc_id:
                                print(machine.machine_id,machine.in_progress, machine.broken)
                        if machine_process_succeed.event.triggered is True:
                            completed = True
                            currently_using.trigger()
                    if n is False:
                        currently_using.trigger()
                if n is True:
                    yield new_try.event
                    currently_using.trigger()
                    n = False

class MoverResource(object):
    def __init__(self, env: simpy.Environment, movers: list):
        self.env = env
        self.movers = movers
        self.resource = simpy.PreemptiveResource(self.env,capacity=len(self.movers))
        self.current_processes = []
        self.number_of_current_proc = 0
        self.resource_type = "mover"

    def request_release_resource(self, get_resource: Event, release_resource: Event,
                                 start_next_proc_step_yield: Event, start_next_proc_step_trigger: Event,
                                 proc_id, product, priority):
        work_done = False
        machine_process_succeed = Event(self.env, False)
        new_try = Event(self.env)
        n = False
        while work_done is False:
            product.monitor.monitor("ASK", self.env.now, "mover")
            flag = False
            if len(self.current_processes) == self.resource.capacity:
                prio, prod, id, current_event = max(self.current_processes, key=lambda item: item[0])
                print(prio, prod, id, current_event)
                proc = prod.processes[id]
                if proc.got_all_resources is False and priority < prio:
                    self.current_processes.remove([prio, prod, id, current_event])
                    flag = True
            with self.resource.request(priority=priority, preempt=flag) as req:
                yield req
                try:
                    t = True
                    currently_using = Event(self.env, False)
                    self.current_processes.append([priority, product, proc_id, currently_using])
                    self.number_of_current_proc += 1
                    if flag is True:
                        if proc.got_all_resources is True and current_event.event is False:
                            yield current_event.event
                            t = False
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
                                                               start_next_proc_step_trigger, new_try))
                                    get_machine = True
                                    break
                        yield release_resource.event
                        work_done = True
                        n = False
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using])
                        self.number_of_current_proc -= 1
                    currently_using.trigger()
                except simpy.Interrupt:
                    if [priority, product, proc_id, currently_using] in self.current_processes:
                        self.current_processes.remove([priority, product, proc_id, currently_using])
                        self.number_of_current_proc -= 1
                    if product.processes[proc_id].got_all_resources is False and n is True:
                        product.processes[proc_id].get_events.remove(get_resource)
                        get_resource = Event(self.env, False)
                        product.processes[proc_id].get_events.append(get_resource)
                        product.processes[proc_id].process_running.interrupt()
                        c.interrupt()
                    currently_using.trigger()
                if n is True:
                    yield new_try.event
                    n = False



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

