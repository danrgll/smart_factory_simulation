import random
import simpy
from base_elements import Event


class Machine(object):
    """A machine that can be initialised as a ring, base or cap station at the same time.
    The set-up times for the different processes are indicated by the different colours of the elements to be
    assembled. The machine is started during initialisation and can be switched off after the simulation of the
    production process has been completed. During this time, faults can occur in the machine, which means that the
    machine is only available again when these have been rectified."""
    def __init__(self, env: simpy.Environment, machine_id: int, machine_type: str, location, repairmen_resource,
                 current_proc_type: list, time_to_change_proc_type: tuple,
                 mean_time_to_failure: float, man_proc_time: list):
        """
        :param env: Environemnt
        :param machine_id: unique id for this resource
        :param machine_type: machine type as a string
        :param location: 2D numpy array for location
        :param repairmen_resource: Resource through which one can request repairmen who in turn can repair
        a fault on the machine.
        :param current_proc_type: list of colors which define a process type
        :param time_to_change_proc_type: Time needed to change individual colour
        :param mean_time_to_failure: Time at which it is 100% likely that the machine will break down
        :param man_proc_time: Times of the different types of production.
        """
        self.env = env
        self.id = machine_id
        self.resource = None  # init in Resource Manager
        self.output = []
        self.machine_type = machine_type
        self.location = location
        self.in_progress = False  # process input
        self.current_process = None  # id from current process
        self.current_product = None
        self.broken = False  # machine status, broken or not
        self.mean_time_to_failure = mean_time_to_failure
        self.repairmen_resource = repairmen_resource
        self.man_proc_time = man_proc_time  # Manufacturing process types time
        self.current_proc_type = current_proc_type  # current process type
        self.time_to_change_proc_type_setting = time_to_change_proc_type  # (mean, sigma)
        self.processing_time_setting = None  # (pt_mean, pt_sigma)
        self.events = {
            "reactivate": Event(self.env),  # activate working
            "wait_until_repaired": Event(self.env),
            "repaired": Event(self.env),
            "end_break": Event(self.env),
            "process_completed": Event(self.env)
        }
        self.data = []  # monitor processes
        self.process = env.process(self.working())
        self.break_process = self.env.process(self.break_machine())
        self.env.process(self.monitor(self.id))
        self.input_process = None
        self.marker = False
        self.kick_process = Event(self.env)

    def input(self, proc_id, get_resource, release_resource_event, start_next_proc_yield: Event,
              start_next_proc_trigger: Event, product, process_suceed, new_try):
        """Pass the new process to the machine and change the process type if necessary. Then waits until the product
        has arrived at the machine and then triggers its production step. While waiting for the product, the process
        can be interrupted if the product is not assigned to the machine next.
        :param proc_id: id of the process
        :param get_resource: Event which signals that the Process got the machine
        :param release_resource_event: Event which signals that the machine finished the work and the process doesent
        need the machine no longer
        :param start_next_proc_yield: wait event until the Product arrived at the machine
        :param start_next_proc_trigger: signals the next resource of the process to start his work
        :param product: product of the process
        :param process_suceed: signals the resource manager that this process part is successfully done
        :param new_try: Event which will be triggered if the Process got interrupted wail waiting. Important for
        resource manager
        """
        try:
            product.monitor.monitor("BEREIT", self.env.now, self.machine_type, self.id)
            loc_update = self.env.process(self.send_location_to_product(product))
            get_resource.trigger()
            self.current_product = product
            self.current_process = proc_id  # hands over the id of the current process
            not_needed_c = self.current_proc_type.copy()
            colors_alrd_avaibl = list()
            for color in product.properties[self.machine_type]:
                if color in not_needed_c:
                    not_needed_c.remove(color)
                    colors_alrd_avaibl.append(color)
            for color in product.properties[self.machine_type]:
                if color not in colors_alrd_avaibl:
                    yield self.env.timeout(self.time_to_change_proc_type())
                    c = not_needed_c.pop()
                    self.current_proc_type.remove(c)
                    self.current_proc_type.append(color)
            self.processing_time_setting = self.man_proc_time[len(product.properties[self.machine_type])-1]
            if start_next_proc_yield.event.triggered is not True:
                yield start_next_proc_yield.event
            self.marker = True
            restart = self.env.process(self.restart_process())
            self.env.process(
                self.finish(restart, release_resource_event, start_next_proc_trigger, product, process_suceed))
            if self.broken is False:
                self.events["reactivate"].trigger()
        except simpy.Interrupt:
            product.monitor.monitor("UNTERBROCHEN BEIM WARTEN", self.env.now, self.machine_type, self.id)
            self.marker = True
            self.in_progress = False
            loc_update.interrupt()
            if self.broken is True:
                release_resource_event.trigger()
            self.marker = False
            new_try.trigger()

    def send_location_to_product(self, product):
        """updated the location of the product"""
        try:
            yield product.events["update_location"].event
            product.stations_location[self.machine_type] = self.location
            product.events[self.machine_type].trigger()
        except simpy.Interrupt:
            return

    def processing_time(self):
        """return the processing_time"""
        return round(abs(random.normalvariate(self.processing_time_setting[0], self.processing_time_setting[1])))

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        fail_at = random.expovariate(self.mean_time_to_failure)
        return round(fail_at)

    def time_to_change_proc_type(self):
        """Return time which machine needs to change proc type"""
        return round(abs(random.normalvariate(self.time_to_change_proc_type_setting[0],
                                              self.time_to_change_proc_type_setting[1])))

    def working(self):
        """Processes pending processes
        While finish a process, the machine may break several times.
        """
        while True:
            try:
                yield self.events["reactivate"].event  # triggered in current_manufacturing_process
                self.current_product.monitor.monitor("STARTE FERTIGUNG", self.env.now, self.machine_type, self.id)
                yield self.env.timeout(self.processing_time())
                self.events["process_completed"].trigger()
            except simpy.Interrupt:
                self.broken = True
                if self.current_product is not None:
                    if self.current_product.processes[self.current_process].got_all_resources is False and \
                            self.in_progress is True and self.marker is False:
                        self.current_product.monitor.monitor("BREAK DER MASCHINE BEIM WARTEN", self.env.now,
                                                             self.machine_type, self.id)
                        req = self.resource.request(priority=-10, preempt=False)
                        self.input_process.interrupt()
                        yield req
                    elif self.in_progress is False:
                        req = self.resource.request(priority=-10, preempt=True)
                        # ToDo was passiert wenn Anfrage zur selbenZeit an Ressource gestellt wird..
                        #  das mit True nocmal testn und überdnekne
                        # ToDo Kann da nicht Blödsinn passieren, gleichzeitige Zuteilung eines Produktes
                        #  sodass Voll und der Kicked danach den falschen
                        # Gefährlich
                        yield req
                    else:
                        self.current_product.monitor.monitor("UNTERBROCHEN IM PROZESS", self.env.now,
                                                             self.machine_type, self.id)
                elif self.in_progress is False:
                    req = self.resource.request(priority=-10, preempt=True)
                    yield req
                self.env.process(self.repairmen_resource.request_release_resource(self.location,
                                                                                  self.events["wait_until_repaired"]))
                yield self.events["wait_until_repaired"].event
                self.broken = False
                if self.in_progress is True:
                    self.events["repaired"].trigger()
                else:
                    self.resource.release(req)
                self.events["end_break"].trigger()

    def restart_process(self):
        """Restarts the manufacturing process if it was interrupted by a fault"""
        while True:
            try:
                yield self.events["repaired"].event
                self.events["reactivate"].trigger()
            except simpy.Interrupt:
                return

    def finish(self, restart, release_resource_event, start_next_proc_trigger, product, proc_succeed):
        """Signals the successful end of the production step. Involved processes are terminated and the
        resource is released again"""
        yield self.events["process_completed"].event
        restart.interrupt()
        self.marker = False
        self.in_progress = False  # signal machine is free
        self.current_product = None
        self.current_process = None
        proc_succeed.trigger()
        self.output.append(product)
        product.monitor.monitor("FERTIG", self.env.now, self.machine_type, self.id)
        release_resource_event.trigger()
        start_next_proc_trigger.trigger()

    def break_machine(self):
        """Break the machine every now and then."""
        try:
            while True:
                yield self.env.timeout(self.time_to_failure())
                self.process.interrupt()
                yield self.events["end_break"].event
        except simpy.Interrupt:
            return

    def monitor(self, machine_id):
        """Monitor processes."""
        while True:
            yield self.events["process_completed"].event
            item = (
                machine_id,
                self.env.now,
                self.current_process
            )
            self.data.append(item)

    def end(self):
        self.break_process.interrupt()
