import base_elements
from base_elements import Event, Process, Resource
import monitor
from machine import Machine
import simpy
import tester
import settings
from product import Product


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        # initialize resources
        self.env = simpy.Environment()
        self.base_station = Resource(self.env,"base", (2, 2), 3, 3)
        self.storage = simpy.Container(self.env, capacity=24)
        self.destination_station = Resource(self.env,"del", (4, 4), 1, 3)
        # initialize mover
        # initialize machines
        self.ring1 = Machine(self.env, 1,"ring", (0, 0), 10.0, 5, 1 / 80, settings.PROC_TIME_RING)
        self.ring2 = Machine(self.env, 2,"ring", (5, 5), 10.0, 5, 1 / 80, settings.PROC_TIME_RING)
        self.cap1 = Machine(self.env, 3, "cap", (10, 10), 10.0, 5, 1 / 80, settings.PROC_TIME_CAP)
        self.cap2 = Machine(self.env, 4,"cap", (10, 5), 10.0, 5, 1 / 80, settings.PROC_TIME_CAP)
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, [self.ring1, self.ring2], 2, "RingBase")
        self.cap_machine_resource = base_elements.MachineResource(self.env, [self.cap1, self.cap2], 2, "CapBase")
        # monitor resources
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station.resource, "pre")
        self.destination_monitor = monitor.MonitorResource(self.env, self.destination_station.resource, "pre")
        # prozess id generator
        self.proc_id_gen = self.process_id_generator()

    def start_simulation(self):
        """starts simulation"""
        self.env.run(until=200)
        print(self.base_station_monitor.data)
        print(self.destination_monitor.data)
        self.base_station_monitor.log_book("monitor_base_station.txt")
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



class ProductionManager:
    # ToDO: strategie implementieren
    def __init__(self, factory, strategy=None):
        self.factory = factory
        self.strategy = strategy

    def produce_c1(self, product: Product):
        """manufactures product"""
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab und liefert es zu Ringstation
        step_base = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                            outputs=[product.events["base_station"]],
                            resources=[self.factory.base_station, self.factory.mover])
        # Ringstation schraubt Ring auf BaseElement
        step_ring = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                            inputs=[product.events["base_station"]],
                            outputs=[product.events["ring_station"]], resources=[self.factory.ring_machine_resource])
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        step_cap = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                           inputs=[product.events["ring_station"]],
                           outputs=[product.events["cap_station"]],
                           resources=[self.factory.mover])
        # Cap_station montiert cap
        step_cap2 = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                            inputs=[product.events["cap_station"]],
                            outputs=[product.events["del_station"]],
                            resources=[self.factory.cap_machine_resource])
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["del_station"]],
                             outputs=[product.events["completed"]],
                             resources=[self.factory.mover, self.factory.destination_station])

    def order(self):
        a = Product(factory.env, 1, settings.PRODUCT_C1)
        b = Product(factory.env, 2, settings.PRODUCT_C1)
        c = Product(factory.env, 3, settings.PRODUCT_C1)
        d = Product(factory.env, 4, settings.PRODUCT_C1)
        e = Product(factory.env, 5, settings.PRODUCT_C1)
        f = Product(factory.env, 6, settings.PRODUCT_C1)
        self.produce_c1(a)
        self.produce_c1(b)
        self.produce_c1(c)
        self.produce_c1(d)
        self.produce_c1(e)
        self.produce_c1(f)



if __name__ == '__main__':
    factory = Factory()
    production_manager = ProductionManager(factory)
    production_manager.order()
    factory.start_simulation()
