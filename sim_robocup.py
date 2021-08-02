import base_elements
from base_elements import Event, Process, Resource
import monitor
from machine import Machine
import simpy
import tester


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        # initialize resources
        self.env = simpy.Environment()
        self.mover = Resource(self.env, 3)
        self.base_station = Resource(self.env, 3)
        self.storage = simpy.Container(self.env, capacity=24)
        self.destination_station = Resource(self.env, 1)
        # initialize machines
        self.ring1 = Machine(self.env, 1, 10.0, 30, 1 / 80, {})
        self.ring2 = Machine(self.env, 2, 10.0, 30, 1 / 80, {})
        self.cap1 = Machine(self.env, 3, 10.0, 30, 1 / 80, {})
        self.cap2 = Machine(self.env, 4, 10.0, 30, 1 / 80, {})
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, [self.ring1, self.ring2], 2, "RingBase")
        self.cap_machine_resource = base_elements.MachineResource(self.env, [self.cap1, self.cap2], 2, "CapBase")
        # monitor resources
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station.resource, "pre")
        self.mover_monitor = monitor.MonitorResource(self.env, self.mover.resource, "pre")
        self.destination_monitor = monitor.MonitorResource(self.env, self.destination_station.resource, "pre")
        # prozess id generator
        self.proc_id_gen = self.process_id_generator()

    def start_simulation(self):
        """starts simulation"""
        self.env.run(until=200)
        print(self.base_station_monitor.data)
        print(self.mover_monitor.data)
        print(self.destination_monitor.data)
        self.base_station_monitor.log_book("monitor_base_station.txt")
        self.mover_monitor.log_book("monitor_mover.txt")
        self.destination_monitor.log_book("monitor_destination.txt")
        print("monitor ring 1")
        print(self.ring1.data)
        print("monitor ring2")
        print(self.ring2.data)
        print("cap1")
        print(self.cap1.data)
        print("cap2")
        print(self.cap2.data)
        print("get resource machine in Prozess, starte Prozess um Maschinen Resource zu erhalten")
        print(tester.d.__next__()-1)
        print("anfrage an machine Resource, aber noch nicht erhalten")
        print(tester.e.__next__() - 1)
        print("machine Resource bekommen")
        print(tester.a.__next__()-1)
        print("machine zugewiesen bekommen")
        print(tester.c.__next__()-1)
        print("current process manu aufgerufen in machine")
        print(tester.b.__next__()-1)
        print("maschine fängt an den Prozess abzuarbeiten")
        print(tester.i.__next__() - 1)
        print("Überprüfe ob Maschine währenddessen kaputt geht")
        print(tester.k.__next__())
        print("maschine hat Prozess abgeschlossen")
        print(tester.g.__next__() - 1)
        print("maschine während laufendem Prozess kaputt gegangen")
        print(tester.f.__next__() - 1)
        print("maschine während laufendem Prozess kaputt gegangen aber noch vor Events")
        print(tester.h.__next__() - 1)
        print("resource maschine wird nach abschluss des prozesses wieder freigegeben")
        print(tester.j.__next__() - 1)
    def process_id_generator(self):
        # ToDO vielleicht eher in Produkt Klasse machen und jedes Produkt verwaltet seine Prozesse nach einer ID
        i = 0
        while True:
            i += 1
            yield i


class Product(object):
    def __init__(self, id: int, factory: Factory):
        self.id = id
        self.factory = factory
        self.env = factory.env
        self.events = {"base_station": Event(self.env),
                       "ring_station": Event(self.env),
                       "cap_station": Event(self.env),
                       "del_station": Event(self.env),
                       "completed": Event(self.env)
                       }
        self.monitor = monitor.MonitorProduct(self.env, self.id, self.events,)  # monitor manufacturing

    def produce(self):
        """manufactures product"""
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab und liefert es zu Ringstation
        step_base = Process(self.env, 10, 1, self.factory.proc_id_gen.__next__(), outputs=[self.events["base_station"]],
                resources=[self.factory.base_station, self.factory.mover])
        # Ringstation schraubt Ring auf BaseElement
        step_ring = Process(self.env, 10, 1, self.factory.proc_id_gen.__next__(), ptype="machine", inputs=[self.events["base_station"]],
                outputs=[self.events["ring_station"]], resources=[self.factory.ring_machine_resource])
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        step_cap = Process(self.env, 10, 1, self.factory.proc_id_gen.__next__(), inputs=[self.events["ring_station"]],
                outputs=[self.events["cap_station"]],
                resources=[self.factory.mover])
        # Cap_station montiert cap
        step_cap2 = Process(self.env, 10, 1, self.factory.proc_id_gen.__next__(), ptype="machine", inputs=[self.events["cap_station"]],
                outputs=[self.events["del_station"]],
                resources=[self.factory.cap_machine_resource])
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.env, 10, 1, self.factory.proc_id_gen.__next__(), inputs=[self.events["del_station"]],
                outputs=[self.events["completed"]],
                resources=[self.factory.mover, self.factory.destination_station])


class ProductionManager:
    # ToDO: strategie implementieren
    def __init__(self, factory, strategy=None):
        self.factory = factory
        self.strategy = strategy

    def order(self):
        a = Product(1, factory)
        b = Product(2, factory)
        c = Product(3, factory)
        d = Product(4, factory)
        e = Product(5, factory)
        f = Product(6, factory)
        a.produce()
        b.produce()
        c.produce()
        d.produce()
        e.produce()
        f.produce()


if __name__ == '__main__':
    factory = Factory()
    production_manager = ProductionManager(factory)
    production_manager.order()
    factory.start_simulation()
