import base_elements
from base_elements import Event, Process, Resource
import monitor
from machine import Machine
import simpy


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
        self.ring1 = Machine(self.env, 1, 20.0, 30, 1 / 500, {})
        self.ring2 = Machine(self.env, 2, 20.0, 30, 1 / 500, {})
        self.cap1 = Machine(self.env, 3, 20.0, 30, 1 / 500, {})
        self.cap2 = Machine(self.env, 4, 20.0, 30, 1 / 500, {})
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, [self.ring1, self.ring2], 2, "RingBase")
        self.cap_machine_resource = base_elements.MachineResource(self.env, [self.cap1, self.cap2], 2, "CapBase")
        # monitor resources
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station.resource, "pre")
        self.mover_monitor = monitor.MonitorResource(self.env, self.mover.resource, "pre")
        self.destination_monitor = monitor.MonitorResource(self.env, self.destination_station.resource, "pre")

    def start_simulation(self):
        """starts simulation"""
        self.env.run(until=200)
        print(self.base_station_monitor.data)
        print(self.mover_monitor.data)
        print(self.destination_monitor.data)
        self.base_station_monitor.log_book("monitor_base_station.txt")
        self.mover_monitor.log_book("monitor_mover.txt")
        self.destination_monitor.log_book("monitor_destination")
        print("monitor ring 1")
        print(self.ring1.data)
        print("monitor ring2")
        print(self.ring2.data)
        print("cap1")
        print(self.cap1.data)
        print("cap2")
        print(self.cap2.data)



    def process_id_generator(self):
        i = 0
        while True:
            yield i + 1


class Product(object):
    # ToDo: Problem lösen das ein Prozess sich sebst abarbeiten muss
    # ToDo: Resource auch in Prozess...und er selbständig wenn gewisse Events erfüllt sind er beginnt Resourcen anzufragen
    # ToDo: bleibt das Problem mit den Maschinen bestehen aber ansonsten eig perfekt
    # ToDo: Klasse Product besteht dann nur aus Prozessen die einmal initialisiert werden aber keiner Reihenfolge untergeordnet sind.
    # ToDO: bedeutet nicht wird geyield, sonder alles funktioniert über Event Steureung
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
        # ToDO: product bekommt eine Event Klasse
        # ToDO: auf die, die Prozesse warten

    def produce(self):
        """manufactures product"""
        # ToDo: request/release anfragen vereinfachen als allgemeine Funktion
        # ToDo: auf einander wartende request anfragen über Events steuern
        # ToDo: Alles über Prozesse steuern?
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab und liefert es zu Ringstation
        step_base = Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), outputs=[self.events["base_station"]],
                resources=[self.factory.base_station, self.factory.mover])
        # Ringstation schraubt Ring auf BaseElement
        step_ring = Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), ptype="machine", inputs=[self.events["base_station"]],
                outputs=[self.events["ring_station"]], resources=[self.factory.ring_machine_resource])
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        step_cap = Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), inputs=[self.events["ring_station"]],
                outputs=[self.events["cap_station"]],
                resources=[self.factory.mover])
        # Cap_station montiert cap
        step_cap2 = Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), ptype="machine", inputs=[self.events["cap_station"]],
                outputs=[self.events["del_station"]],
                resources=[self.factory.cap_machine_resource])
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), inputs=[self.events["del_station"]],
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
        c = Product(4, factory)
        d = Product(5, factory)
        e = Product(6, factory)
        f = Product(7, factory)
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
    print("Ende")
