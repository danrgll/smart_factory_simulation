import construction
import monitor
import simpy


class Factory:
    """create amount of resources(machines)"""
    def __init__(self):
        self.env = simpy.Environment()
        self.mover = simpy.Resource(self.env, capacity=3)
        self.base_station = simpy.Resource(self.env, capacity=3)
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station, "pre")
        self.storage = simpy.Container(self.env, capacity=24)
        self.destination_station = simpy.Resource(self.env, capacity=1)
        self.ring1 = construction.Machine(self.env, 1, 20.0, 30, 1/50, {})
        self.ring2 = construction.Machine(self.env, 2, 20.0, 30, 1/50, {})
        self.cap1 = construction.Machine(self.env, 3, 20.0, 30, 1/50, {})
        self.cap2 = construction.Machine(self.env, 4, 20.0, 30, 1/50, {})
        self.ring_machine_resource = construction.MachineResource(self.env, [self.ring1, self.ring2], 2, "RingBase")
        self.cap_machine_resource = construction.MachineResource(self.env, [self.cap1, self.cap2], 2, "CapBase")
        self.env.process(self.product(1))
        self.env.process(self.product(2))
        self.env.process(self.product(3))
        self.env.process(self.product(4))

    def start_simulation(self):
        """starts simulation"""
        self.env.run(until=1000)
        print(self.base_station_monitor.data)
        self.base_station_monitor.log_book("monitor_base_station.txt")

    def process_id_generator(self):
        i = 0
        while True:
            yield i+1

    def product(self, id):
        """manufactures product"""
        # ToDo: request/release anfragen vereinfachen als allgemeine Funktion
        # ToDo: auf einander wartende request anfragen über Events steuern
        # ToDo: Alles über Prozesse steuern?
        # ToDo: Monitor Processes
        tracing = monitor.MonitorProduct()
        # Anfragen ob BaseStation frei
        request_base = self.base_station.request()
        yield request_base
        log = f"product {id} occupied BaseStation at {self.env.now}"
        tracing.data.append(log)
        print(log)
        # anfragen ob Mover frei
        request_mover = self.mover.request()
        yield request_mover
        log = f"product {id} occupied Mover at {self.env.now}"
        tracing.data.append(log)
        print(log)
        # Mover fährt zu BaseStation und holt BaseElement ab
        yield self.env.timeout(30)
        self.base_station.release(request_base)
        log = f"product {id} release BaseStation at {self.env.now}"
        tracing.data.append(log)
        print(log)
        # Anfrage ringstation
        r_process = construction.Process(self.env, 10, 1, self.process_id_generator().__next__(), None)
        ring_process = self.env.process(self.ring_machine_resource.request_release_resource(r_process))
        # Zeit um zu RingStation hinzufahren
        yield self.env.timeout(5)
        self.mover.release(request_mover)
        log = f"product {id} release Mover at {self.env.now}"
        tracing.data.append(log)
        print(log)
        yield ring_process
        log = f"product {id} has assembled ring on base at {self.env.now}"
        tracing.data.append(log)
        print(log)
        # Anfrage an Mover abholen um zu cap zugelangen
        request_mover = self.mover.request()
        yield request_mover
        # Mover fährt zu cap und capStation added cap
        c_process = construction.Process(self.env, 10, 1, self.process_id_generator().__next__(), None)
        cap_process = self.env.process(self.cap_machine_resource.request_release_resource(c_process))
        yield self.env.timeout(5)
        self.mover.release(request_mover)
        yield cap_process
        tracing.data.append(log)
        print(f"product {id} hat cap aufgesetzt at {self.env.now}")
        # Anfrage an Mover um zu Zieldestination anzukommen
        request_mover = self.mover.request()
        yield request_mover
        request_destination_base = self.destination_station.request()
        yield request_destination_base
        # Product wandert zur Zielausgabe
        yield self.env.timeout(10)
        self.mover.release(request_mover)
        self.destination_station.release(request_destination_base)
        tracing.data.append(log)
        print(f"product {id} has been completed at {self.env.now}")


if __name__ == '__main__':
    factory = Factory()
    factory.start_simulation()
    print("Ende")
