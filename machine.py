import random
import tester
from itertools import count
import simpy
from base_elements import Event
from product import Product

class Machine(object):
    # ToDO: Processingtime auslagern, nicht von Prozess bestimmen lassen sondern vom Porzesstyp.
    #  Jede MAchine unterschiedlich vielleicht
    # in eigene Datei verschwiende Config Speichern für Maschinen, welche Prozesse, wie lange brauchen
    """Machines that process something"""
    def __init__(self, env: simpy.Environment, machine_id, machine_type, location, repair_time: float, time_to_change_proc_type: float,
                 mean_time_to_failure: float, man_proc_time: list):
        # ToDo: man_proc noch nicht in Verwendung, proc_type noch nicht verwendet
        self.env = env
        self.machine_id = machine_id
        self.resource = None  # init in Resource Manager
        self.output = []
        self.machine_type = machine_type
        self.location = location
        self.in_progress = False  # process input
        self.active_process = False
        self.current_process = None  # id from current process
        self.broken = False  # machine status, broken or not
        self.mean_time_to_failure = mean_time_to_failure
        self.repair_time = repair_time
        self.man_proc_time = man_proc_time  # Manufacturing process types time
        self.current_proc_type = None  # current process type
        self.time_to_change_proc_type = time_to_change_proc_type
        self.processing_time_setting = None  # (pt_mean, pt_sigma)
        self.events = {
            "reactivate": Event(self.env),  # activate working
            "repaired": Event(self.env),  # machine breaks
            "process_completed": Event(self.env),
            "kick_process": Event(self.env)  # machine completed the process
        }
        self.data = []  # monitor processes
        self.process = env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor(self.machine_id))


    def input(self, proc_id, release_resource_event, start_next_proc_yield, start_next_proc_trigger: Event, product: Product):
        """Pass the new process to the machine and change the process type if necessary"""
        print("testmachine")
        tester.b.__next__()
        product.stations_location[self.machine_type] = self.location
        product.events[self.machine_type].trigger()
        self.current_process = proc_id  # hands over the id of the current process
        #ToDO: current proc_type macht keinen Sinn, 3 Farben initialisieren und mit denen sollte dann einzeln Verglichen werden die [properties]
        if self.current_proc_type != product.properties[self.machine_type]:
            self.current_proc_type = product.properties[self.machine_type]
            yield self.env.timeout(self.time_to_change_proc_type)  # time to change machine config to process new process type
        self.processing_time_setting = self.man_proc_time[len(product.properties[self.machine_type])-1]
        #ToDO: Dict in Produkt klasse not_porcessed yet aufmachen??
        restart = self.env.process(self.restart_process())
        self.env.process(self.finish(restart, release_resource_event, start_next_proc_trigger, product))
        yield start_next_proc_yield.event
        if self.broken is True:
            tester.h.__next__()
        else:
            self.events["reactivate"].trigger()
        self.env.process(self.restart_process())

    def processing_time(self):
        """return the processing_time"""
        return random.normalvariate(self.processing_time_setting[0], self.processing_time_setting[1])

    def time_to_failure(self):
        """Return time until next failure for a machine."""
        fail_at = random.expovariate(self.mean_time_to_failure)
        return fail_at

    def working(self):
        """Processes pending processes
        While finish a process, the machine may break several times.
        """
        while True:
            try:
                yield self.events["reactivate"].event  # triggered in current_manufacturing_process
                tester.i.__next__()
                yield self.env.timeout(self.processing_time()) # ToDo: Prozess mit mehreren Resourcen. Processing Time falsch
                # yield in process def running ToDo noch nicht Optimal. Wenn Process Mover und Machine
                # ToDo: bekommen hat beginnt er einfach abzuarbeiten,proc_event kann so bleiben aber in Mover noch Event implementieren
                self.events["process_completed"].trigger()
            except simpy.Interrupt:
                self.broken = True
                if self.in_progress is False:
                    req = self.resource.request(priority=-1)
                    yield req
                print(f"machine {self.machine_id} breaks @t={self.env.now}")
                yield self.env.timeout(self.repair_time)
                print(f"machine {self.machine_id} ready again @t={self.env.now}")
                self.broken = False
                if self.in_progress is True:
                    tester.f.__next__()
                    self.events["repaired"].trigger()
                else:
                    self.resource.release(req)

    def restart_process(self):
        #ToDO: überlegen ob hier durch aufrufe etwas blödes passieren kann. wird aufgerufen zum
        # Beispiel nachdem es von einem Prozess zuvor losgetreten wurde. Muss auch zum Ende kommen
        while True:
            try:
                yield self.events["repaired"].event
                tester.k.__next__()
                self.env.timeout(5)
                self.events["reactivate"].trigger()
            except simpy.Interrupt:
                return


    def finish(self, restart, release_resource_event, start_next_proc_trigger, product):
        yield self.events["process_completed"].event
        tester.g.__next__()
        restart.interrupt()
        self.in_progress = False  # signal machine is free
        self.output.append(product)
        product.monitor_product.trigger()
        release_resource_event.trigger()
        start_next_proc_trigger.trigger()
        print("Maschine fertig")


    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            self.process.interrupt()
            yield self.events["repaired"].event

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
            print(f"machine {machine_id} completed process @t={self.env.now}")