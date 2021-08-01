import random
import simpy
from simpy import AllOf


class Event(object):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.event = simpy.Event(self.env)

    def trigger(self, value=None, reuse=True):
        """trigger self.event and if we want to use this event again create a new simpy.Event"""
        print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        if reuse is True:
            self.event = simpy.Event(self.env)


class Process(object):
    # ToDo: schauen welche Events wir nochmal benötigen. Falls nicht reuse=False setzen
    # ToDO: Problem der prozesszeit wenn zwei Resourcen benötigt werden. Mover und dann Maschine. Prozesszeit komplett rausnehemen, sie macht einfach keinen Sinn
    # ToDo: Prozesszeit von ganz anderen Dingen abhängig. MAschine muss selber wissen wie lange sie braucht. sowie der Mover auch.
    def __init__(self, env, pt_mean, pt_sigma, pid, ptype=None, process_machine_type=None, inputs=None, outputs=None, resources=None):
        self.env = env
        self.pt_mean = pt_mean
        self.pt_sigma = pt_sigma
        self.process_id = pid
        self.process_type = ptype
        self.process_machine_type = process_machine_type
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
        self.release_events = list()
        self.proc_event = Event(self.env)  # Event which mark if the Process are processed
        self.data = []
        self.process = self.env.process(self.check_input_events())

    def check_input_events(self):
        yield AllOf(self.env, [x.event for x in self.inputs])
        self.get_resources()

    def get_resources(self):
        # ToDO: Problem bei Maschinen als Resource..andere parameter bei release_request Funktion
        """calls for required resources"""
        for resource in self.resources:
            print(resource)
            get_event = Event(self.env)
            release_event = Event(self.env)
            self.get_events.append(get_event)
            self.release_events.append(release_event)
            if self.process_type == "machine":
                print("machine")
                self.env.process(resource.request_release_resource(get_event, release_event, self.proc_event, self.process_id, self.process_type,
                                                          self.processing_time()))
            # ToDO: release Event einabuen noch gescheit, speichern in Liste von Nöten?
            else:
                print("normal resource")
                self.env.process(resource.request_release(get_event, release_event))
        print("test3")
        self.process = self.env.process(self.running())

    def running(self):
        print("test4")
        # ToDO: Problem verschiedene Prozesse Machine und keine Maschine unter einen Hut zubekommen
        #ToDO: ProzessZeit rausnehmen. über event steuerung und Prozesszeit über die verwendete Resource steuern
        # wait until process got all resources which needed
        yield AllOf(self.env, [x.event for x in self.get_events])
        print("test5")
        if self.process_type == "machine":
            print("machine_start")
            yield self.proc_event.event  # wait until machine processed the process
            print("machine fertig")
        else:
            yield self.env.timeout(self.processing_time())
        for event in self.release_events:
            event.trigger()
        for o in self.outputs:
            o.trigger(value=self.process_id)

    def processing_time(self):
        """Returns actual processing time."""
        return random.normalvariate(self.pt_mean, self.pt_sigma)


class Resource(object):
    def __init__(self, env: simpy.Environment, capacity: int):
        self.env = env
        self.resource = simpy.Resource(self.env, capacity)

    def request_release(self, get_resource: Event, release_resource: Event):
        # ToDo: wo wird event getriggered?? in Klasse Proccesses als Output gute Möglichkeit
        # ToDo: Halte Resource solange sie benötigt wird
        """request and hold resource. After event is triggered release resource"""
        print("test6")
        request = self.resource.request()
        yield request
        get_resource.trigger()  # event to signal that you get the resource
        yield release_resource.event
        self.resource.release(request)


class MachineResource:
    """manages a amount of produced machines as a resource"""
    def __init__(self, env: simpy.Environment, machines: list, capacity: int, machine_type: str):
        self.env = env
        self.machines = machines
        self.resource = simpy.Resource(self.env, capacity)
        self.machine_type = machine_type
        print("init MachineResource")

    def request_release_resource(self, get_resource: Event, release_resource: Event, proc_event: Event,
                                 proc_id, process_type, processing_time):
        request = self.resource.request()
        yield request
        self.print_stats(self.resource)
        for machine in self.machines:
            # ToDo: was ist wenn machine broken und somit weniger machinen zur Verfügung stehen. Lösung über Events oder
            # ToDo: while True Schleife
            if machine.input is False:
                machine.input = True
                get_resource.trigger()
                # ToDo: irg was stimmt hier nicht unterschiedliche anzahl von Prodkuten kommen am Ziel an?? Vielleicht Fehler ToDO oben drüber. Könnte sehr gut sein
                self.env.process(machine.current_manufacturing_process(proc_id, proc_event, process_type, processing_time))  # übergebe process an maschine
                break
        self.print_stats(self.resource)
        yield release_resource.event
        self.resource.release(request)
        self.print_stats(self.resource)

    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at {self.machine_type}.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')
