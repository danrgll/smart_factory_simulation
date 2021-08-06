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
        self.machine_type = machine_type
        self.coordinates = location
        self.ready = True  # process input
        self.active_process = False
        self.current_process = None  # id from current process
        self.broken = False  # machine status, broken or not
        self.mean_time_to_failure = mean_time_to_failure
        self.repair_time = repair_time
        self.man_proc_time = man_proc_time  # Manufacturing process types time
        self.current_proc_type = None  # current process type
        self.time_to_change_proc_type = time_to_change_proc_type
        self.processing_time = None
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

    def input(self, proc_id, release_resource_event, product: Product):
        """Pass the new process to the machine and change the process type if necessary"""
        print("testmachine")
        tester.b.__next__()
        self.ready = False
        self.current_process = proc_id  # hands over the id of the current process
        if self.current_proc_type != product.properties[self.machine_type]:
            self.current_proc_type = product.properties[self.machine_type]
            yield self.env.timeout(self.time_to_change_proc_type)  # time to change machine config to process new process type
        self.env.process(self.finish(release_resource_event))
        # ToDO: yield product kommt an abwarten bis dahin
        self.events["reactivate"].trigger()
        self.env.process(self.restart_process())


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
                yield self.env.timeout(self.processing_time) # ToDo: Prozess mit mehreren Resourcen. Processing Time falsch
                # yield in process def running ToDo noch nicht Optimal. Wenn Process Mover und Machine
                # ToDo: bekommen hat beginnt er einfach abzuarbeiten,proc_event kann so bleiben aber in Mover noch Event implementieren
                self.events["process_completed"].trigger()
            except simpy.Interrupt:
                self.broken = True
                if self.ready is True:
                    pass
                    # ToDo: drücke request einer Resource rein prio damit kein Process resource bekommt.
                print(f"machine {self.machine_id} breaks @t={self.env.now}")
                yield self.env.timeout(self.repair_time)
                print(f"machine {self.machine_id} ready again @t={self.env.now}")
                self.broken = False
                if self.ready is True:
                    self.events["repaired"].trigger()

    def restart_process(self):
        #ToDO: überlegen ob hier durch aufrufe etwas blödes passieren kann. wird aufgerufen zum
        # Beispiel nachdem es von einem Prozess zuvor losgetreten wurde. Muss auch zum Ende kommen
        yield self.events["repaired"].event
        self.env.timeout(2)
        self.events["reactivate"].trigger()

    def finish(self,release_resource_event):
        yield self.events["process_completed"].event
        tester.g.__next__()
        self.ready = True  # signal machine is free
        release_resource_event.trigger()

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