import random
import simpy
import tester
from product import Product
from simpy import AllOf


class Event(object):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.event = simpy.Event(self.env)

    def trigger(self, value=None, reuse=True):
        """trigger self.event and if we want to use this event again create a new simpy.Event"""
        # print("event #%s triggered @t=%f" % (value, self.env.now))
        self.event.succeed(value=value)
        if reuse is True:
            self.event = simpy.Event(self.env)



class Process(object):
    # ToDo: schauen welche Events wir nochmal benötigen. Falls nicht reuse=False setzen
    # ToDO: Problem der prozesszeit wenn zwei Resourcen benötigt werden. Mover und dann Maschine. Prozesszeit komplett rausnehemen, sie macht einfach keinen Sinn
    # ToDo: Prozesszeit von ganz anderen Dingen abhängig. MAschine muss selber wissen wie lange sie braucht. sowie der Mover auch.
    # ToDO: Product jeder Resource mitgeben, damit diese weis mit welchem Product arbeite ich gerade
    def __init__(self, env, product, pid, inputs=None, outputs=None, resources=None):
        self.env = env
        self.process_id = pid
        self.product = product
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
        yield AllOf(self.env, [x.event for x in self.inputs])
        self.env.process(self.running())
        self.get_resources()

    def get_resources(self):
        """calls for required resources"""
        # Lösung der Resourcen reihenfolge anfragen. So in liste geben wie man es auch gerne nutzen würde.
        # sann jeweils event übergeben das erst getriggerd werden muss bevor eine weitere Resource angefragt wird.
        start_next_proc_step = None
        for resource in self.resources:
            get_event = Event(self.env)
            release_event = Event(self.env)
            self.get_events.append(get_event)
            # ToDO: Problem beginnt direkt abzuarbeiten womöglich noch bevor er alle resourcen bekommt.
            tester.d.__next__()
            # resource machine
            self.env.process(resource.request_release_resource(get_event, release_event, start_next_proc_step, self.process_id, self.product))
            start_next_proc_step = Event(self.env)
            self.process_steps_events.append(start_next_proc_step)

    def running(self):
        # ToDo: Hier werden die einzelnen Resourcen abgearbeotet und wieder freigegeben am Ende wird das Output event getriggerd
        #ToDO: ProzessZeit rausnehmen. über event steuerung und Prozesszeit über die verwendete Resource steuern
        # wait until process got all resources which needed.weiteres problm..hier sollten prozesse erst gestartet werden in einer spezifischen reihenfolge
        # resourcennutzungs reihenfolge relevant. erst maschine, dann mover anfragen.
        yield AllOf(self.env, [x.event for x in self.get_events])
        self.process_steps_events.pop(0).trigger()  # trigger event to start first process step
        yield AllOf(self.env, [x.event for x in self.process_steps_events])
        for o in self.outputs:
            o.trigger(value=self.process_id)


class Resource(object):
    def __init__(self, env: simpy.Environment, location, capacity: int, processing_time):
        self.env = env
        self.location = location
        self.resource = simpy.Resource(self.env, capacity)
        self.resource_type = "standard"
        self.processing_time = processing_time

    def request_release(self, get_resource: Event, release_resource: Event, start_next_proc_step: Event, proc_id, product: Product):
        # ToDo: wo wird event getriggered?? in Klasse Proccesses als Output gute Möglichkeit
        # ToDo: Halte Resource solange sie benötigt wird
        """request and hold resource. After event is triggered release resource"""
        request = self.resource.request()
        yield request
        get_resource.trigger() # event to signal that you get the resource
        # ToDo yield event was Prozess startet. gesteuert über Product.
        yield self.env.timeout(self.processing_time)
        yield release_resource.event
        self.resource.release(request)




class MachineResource:
    """manages a amount of produced machines as a resource"""
    def __init__(self, env: simpy.Environment, machines: list, capacity: int, machine_type: str):
        self.env = env
        self.machines = machines
        self.resource = simpy.Resource(self.env, capacity)
        self.resource_type = "machine"
        self.machine_type = machine_type

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step,
                                 proc_id, product: Product):
        request = self.resource.request()
        tester.e.__next__()
        yield request

        print("getResource")
        tester.a.__next__()
        self.print_stats(self.resource)
        get_machine = False
        # ToDO: können wir nicht so machen. Komme in Endlosschleife...Prio auch keine gute idee weil was ist wenn alle Resourcen im letzten Moment besetzt.
        # ToDo: kicke womöglich falschen Prozess.herausfinden ob man Prozess auswählen kann..denke aber nicht fuck
        # Irg wie über yield event lösen...
        while get_machine is False:
            for machine in self.machines:
                # ToDO: Maschine kein Input und geht kaputt. Sollte keine weiteren Prozesse erhalten in der Zeit. Übergebe resource und belege diese solange. Prio Resource? Lösung weil
                # Ohne das Problem, dass es sich womöglich anstellt..aber muss mir P<rio dafür nochmal genau anschauen ob es das Probklem lösen könnte
                if machine.ready is True and machine.broken is False:
                    tester.c.__next__()
                    machine.ready = True
                    get_resource.trigger()  # auslagern in Maschine
                    self.env.process(machine.input(proc_id, release_resource, product))  # übergebe process an maschine
                    get_machine = True
                    break
        yield release_resource.event
        tester.j.__next__()
        self.resource.release(request)
        self.print_stats(self.resource)

    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at {self.machine_type}.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')


class MoverResource():
    def __init__(self, env: simpy.Environment, mover: list, capacity: int):
        self.env = env
        self.mover = mover
        self.resource = simpy.Resource(self.env,capacity=capacity)
        self.resource_type = "mover"

    def request_release_resource(self, get_resource: Event, release_resource: Event, start_next_proc_step: Event,
                                 proc_id, product: Product):
        pass

    def print_stats(self, res):
        print(f'{res.count} of {res.capacity} slots are allocated at {self.machine_type}.')
        # print(f'  Users: {res.users}')
        # print(f'  Queued events: {res.queue}')



