import base_elements
from base_elements import Event, Process, Resource
import monitor
import simpy


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        self.env = simpy.Environment()
        self.mover = Resource(self.env, 3)
        self.base_station = Resource(self.env, 3)
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station, "pre")
        self.storage = simpy.Container(self.env, capacity=24)
        self.destination_station = Resource(self.env, 1)
        self.ring1 = base_elements.Machine(self.env, 1, 20.0, 30, 1 / 50, {})
        self.ring2 = base_elements.Machine(self.env, 2, 20.0, 30, 1 / 50, {})
        self.cap1 = base_elements.Machine(self.env, 3, 20.0, 30, 1 / 50, {})
        self.cap2 = base_elements.Machine(self.env, 4, 20.0, 30, 1 / 50, {})
        self.ring_machine_resource = base_elements.MachineResource(self.env, [self.ring1, self.ring2], 2, "RingBase")
        self.cap_machine_resource = base_elements.MachineResource(self.env, [self.cap1, self.cap2], 2, "CapBase")

    def start_simulation(self):
        """starts simulation"""
        self.env.run(until=1000)
        print(self.base_station_monitor.data)
        self.base_station_monitor.log_book("monitor_base_station.txt")

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
                       "wait_for_transport": Event(self.env),
                       "ring_station": Event(self.env),
                       "cap_station": Event(self.env),
                       }
        self.monitor = monitor.MonitorProduct()  # monitor manufacturing
        # ToDO: product bekommt eine Event Klasse
        # ToDO: auf die, die Prozesse warten

    def produce(self):
        """manufactures product"""
        # ToDo: request/release anfragen vereinfachen als allgemeine Funktion
        # ToDo: auf einander wartende request anfragen über Events steuern
        # ToDo: Alles über Prozesse steuern?
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab
        print("test1")
        base_station = Event(self.env)
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), outputs=[base_station],
                resources=[self.factory.base_station, self.factory.mover])
        # Mover fährt zu RingStation und liefert BaseElement ab
        ring_station = Event(self.env)
        # ToDo: Möchte immernoch gleichen Mover nutzen können aber BaseSttion natürlich frtei geben
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), inputs=[base_station],
                outputs=[ring_station], resources=[self.factory.mover])
        # Ringstation schraubt Ring auf BaseElement
        # ToDO: Nutung von MAchine Resource noch nicht garantiert
        rdy_for_cap_station = Event(self.env)
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), ptype="machine", inputs=[ring_station],
                outputs=[rdy_for_cap_station], resources=[self.factory.ring_machine_resource])
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        cap_station = Event(self.env)
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), inputs=[rdy_for_cap_station],
                outputs=[cap_station],
                resources=[self.factory.mover])
        # Cap_station montiert cap
        completed = Event(self.env)
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), ptype="machine", inputs=[cap_station],
                outputs=[completed],
                resources=[self.factory.cap_machine_resource])
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        Process(self.env, 10, 1, self.factory.process_id_generator().__next__(), inputs=[completed],
                outputs=[completed],
                resources=[self.factory.mover, self.factory.destination_station])
        print("test2")


class ProductionManager:
    # ToDO: strategie implementieren
    def __init__(self, factory, strategy=None):
        self.factory = factory
        self.strategy = strategy

    def order(self):
        a = Product(1, factory)
        b= Product(2, factory)
        a.produce()
        b.produce()


if __name__ == '__main__':
    factory = Factory()
    production_manager = ProductionManager(factory)
    production_manager.order()
    factory.start_simulation()
    print("Ende")
