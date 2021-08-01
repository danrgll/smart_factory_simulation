import random
from itertools import count
import simpy
from base_elements import Event

class Machine(object):
    # ToDO: Event einbauen aus Processklasse welches markiert ob der Prozess abggearbeiitet ist.
    # ToDO: Processingtime auslagern, nicht von Prozess bestimmen lassen sondern vom Porzesstyp.
    #  Jede MAchine unterschiedlich vielleicht
    """Machines that process something"""
    def __init__(self, env: simpy.Environment, machine_id, repair_time: float, time_to_change_proc_type,
                 mean_time_to_failure: float, man_proc: dict):
        # ToDo: man_proc noch nicht in Verwendung, proc_type noch nicht verwendet
        self.env = env
        self.machine_id = machine_id
        self.input = False  # process input
        self.current_process = None  #id from current process
        self.broken = False  # machine status, broken or not
        self.mean_time_to_failure = mean_time_to_failure
        self.repair_time = repair_time
        self.man_proc = man_proc  # Manufacturing process types
        self.current_proc_type = None  # current process type
        self.time_to_change_proc_type = time_to_change_proc_type
        self.processing_time = None
        self.events = {
            "reactivate": Event(self.env),  # activate working
            "repaired": Event(self.env),  # machine breaks
            "process_completed": Event(self.env),  # machine completed the process
        }
        self.proc_event = None
        self.data = []  # monitor processes
        self.process = env.process(self.working())
        self.env.process(self.break_machine())
        self.env.process(self.monitor(self.machine_id))

    def current_manufacturing_process(self,proc_id, proc_event, process_type, processing_time):
        """Pass the new process to the machine and change the process type if necessary"""
        self.input = True
        self.current_process = proc_id  # hands over the id of the current process
        self.proc_event = proc_event
        self.processing_time = processing_time
        yield self.env.timeout(1)
        if self.current_proc_type != process_type:
            self.current_proc_type = process_type
            yield self.env.timeout(3)  # time to change machine config to process new process type
        self.env.process(self.finish())
        self.events["reactivate"].trigger()
        while input is True:
            if self.broken is True:
                yield self.events["repaired"].event
                self.env.timeout(3)
                self.events["reactivate"].trigger()


    def time_to_failure(self):
        """Return time until next failure for a machine."""
        fail_at = random.expovariate(self.mean_time_to_failure)
        print(f"machine {self.machine_id} will fail at {fail_at}")
        return fail_at

    def working(self):
        """Processes pending processes
        While finish a process, the machine may break several times.
        """
        print("start working")
        while True:
            # ToDo: Überprüfen on nach interupt der Prozess trotzdem noch abgearbeitet wird
            # ToDo: Gedanken über Events machen/Running funktion sinnvoll?
            # ToDo: Weil wir nicht interrupted vermutlich
            try:
                yield self.events["reactivate"].event  # triggered in current_manufacturing_process
                print("activate machine")
                yield self.env.timeout(self.processing_time) # ToDo: Prozess mit mehreren Resourcen. Processing Time falsch
                # yield in process def running ToDo noch nicht Optimal. Wenn Process Mover und Machine
                # ToDo: bekommen hat beginnt er einfach abzuarbeiten,proc_event kann so bleiben aber in Mover noch Event implementieren
                self.events["process_completed"].trigger()
            except simpy.Interrupt:
                self.broken = True
                print(f"machine {self.machine_id} breaks @t={self.env.now}")
                yield self.env.timeout(self.repair_time)
                print(f"machine {self.machine_id} ready again @t={self.env.now}")
                self.events["repaired"].trigger()
                self.broken = False

    def finish(self):
        yield self.events["process_completed"].event
        print("Prozess beendet")
        self.proc_event.trigger()
        self.input = False




    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                self.process.interrupt()

    def monitor(self, machine_id):
        """Monitor processes."""
        print("start monitor")
        for process in count():
            yield self.events["process_completed"].event
            item = (
                machine_id,
                process,
                self.env.now,
                self.current_process
            )
            self.data.append(item)
            print(f"machine {machine_id} completed process {process} @t={self.env.now}")