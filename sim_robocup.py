import construction
import simpy


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        self.env = simpy.Environment()
        self.mover = simpy.Resource(capacity=3)
        self.base_station = simpy.Resource(capacity=3)
        self.storage = simpy.Container(capacity=24)
        self.destination_station = simpy.Resource(capacity=1)
        self.ring1 = construction.Machine(self.env, 1, 20.0, 30, 50, {})
        self.ring2 = construction.Machine(self.env, 1, 20.0, 30, 50, {})
        self.cap1 = construction.Machine(self.env, 1, 20.0, 30, 50, {})
        self.cap2 = construction.Machine(self.env, 1, 20.0, 30, 50, {})
        self.ring_machine_resource = construction.MachineResource(self.env, [self.ring1, self.ring2], 2)
        self.cap_machine_resource = construction.MachineResource(self.env, [self.cap1, self.cap2], 2)
        self.env.process(self.product(1))
        self.env.process(self.product(2))
        self.env.process(self.product(3))
        self.env.process(self.product(4))

    def start_simulation(self):
        print("start_simluation")
        self.env.run(until=1000)
        print("sim started")

    def product(self, id):
        # Anfragen ob BaseStation frei
        request_base = self.base_station.request()
        yield request_base
        print(f"product {id} belegt BaseStation")
        # anfragen ob Mover frei
        request_mover = self.mover.request()
        yield request_mover
        print(f"product {id} belegt Mover")
        # Mover fährt zu BaseStation und holt BaseElement ab
        self.env.timeout(30)
        self.base_station.release(request_base)
        #Anfrage ringstation
        ring_process = self.env.process(self.ring_machine_resource.request_release_resource())
        # Zeit um zu RingStation hinzufahren
        self.env.timeout(5)
        self.mover.release(request_mover)
        yield ring_process
        print(f"product {id} hat ring auf base geschraubt")
        #Anfrage an Mover abholen um zu cap zugelangen
        request_mover = self.mover.request()
        yield request_mover
        #Mover fährt zu cap und capStation added cap
        cap_process = self.env.process(self.cap_machine_resource.request_release_resource())
        self.env.timeout(5)
        self.mover.release(request_mover)
        yield cap_process
        print(f"product {id} hat cap aufgesetzt")
        # Anfrage an Mover um zu Zieldestination anzukommen
        request_mover = self.mover.request()
        yield request_mover
        request_destination_base = self.destination_station.request()
        yield request_destination_base
        # Product wandert zur Zielausgabe
        self.env.timeout(10)
        self.mover.release(request_mover)
        self.destination_station.release(request_destination_base)
        print(f"product {id} has been completed")

if __name__ == '__main__':
    factory = Factory()
    factory.start_simulation()
    print("Ende")