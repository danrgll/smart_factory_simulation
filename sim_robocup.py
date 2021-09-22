import base_elements
from base_elements import Event, Process, Resource
import monitor
from repairman import Repairman
from machine import Machine
from mover import Mover
import simpy
import tester
from settings import *
import strategy
import plot
from statistic import Stat, FileNameGenerator,MeanStat

# ToDO: mögliche Priority bei den Masdchinen Resourcen wieder rausnehmen wenn nicht benötigt.
class SmartFactory:
    """create amount of resources(machines)"""
    def __init__(self):
        # initialize enviroment
        self.env = simpy.Environment()
        # initialize basic resources
        #self.base_station = Resource(self.env, "base", settings.base_location, 3, settings.PROC_TIME_BASE)
        #self.storage = simpy.Container(self.env, capacity=24)
        self.destination_station = Resource(self.env,"del", DEL_LOCATION, 1, PROC_TIME_DEL)
        # initialize repairman
        self.repairman1 = Repairman(self.env, REPAIRMEN_LOCATION, REPAIR_TIME)
        self.repairman2 = Repairman(self.env, REPAIRMEN_LOCATION, REPAIR_TIME)
        # self.repairman3 = Repairman(self.env, REPAIRMEN_LOCATION, REPAIR_TIME)
        # group repairmen
        self.repairmen_resource = base_elements.RepairmenResource(self.env,
                                                                  [self.repairman1, self.repairman2])

        # initialize base
        self.base1 = Machine(self.env, 1, "base", BASE_LOCATION, self.repairmen_resource, PROC_TYPE_INIT_BS, TIME_TO_CHANGE_PROC_TYPE_BS, MEAN_TIME_TO_FAILURE_BS, PROC_TIME_BASE)
        self.base_machine_resource = base_elements.MachineResource(self.env, [self.base1],
                                                                   "BaseStation")
        # initialize mover
        self.mover1 = Mover(self.env,1 , MOVER_LOCATION1, TIME_TO_PICK_UP)
        self.mover2 = Mover(self.env,2,  MOVER_LOCATION2, TIME_TO_PICK_UP)
        self.mover3 = Mover(self.env,3,  MOVER_LOCATION3, TIME_TO_PICK_UP)
        # group movers
        self.mover_resource = base_elements.MoverResource(self.env, [self.mover1, self.mover2, self.mover3])
        # initialize machines
        self.ring1 = Machine(self.env, 1, "ring", RING_LOCATION1, self.repairmen_resource, PROC_TYPE_INIT_RS, TIME_TO_CHANGE_PROC_TYPE_RS, MEAN_TIME_TO_FAILURE_RS, PROC_TIME_RING)
        self.ring2 = Machine(self.env, 2, "ring", RING_LOCATION2, self.repairmen_resource, PROC_TYPE_INIT_RS, TIME_TO_CHANGE_PROC_TYPE_RS, MEAN_TIME_TO_FAILURE_RS, PROC_TIME_RING)
        # self.ring3 = Machine(self.env, 3, "ring", RING_LOCATION3, self.repairmen_resource, PROC_TYPE_INIT_RS, TIME_TO_CHANGE_PROC_TYPE_RS, MEAN_TIME_TO_FAILURE_RS, PROC_TIME_RING)
        self.cap1 = Machine(self.env, 1, "cap", CAP_LOCATION1, self.repairmen_resource, PROC_TYPE_INIT_CS, TIME_TO_CHANGE_PROC_TYPE_CS, MEAN_TIME_TO_FAILURE_CS, PROC_TIME_CAP)
        self.cap2 = Machine(self.env, 2, "cap", CAP_LOCATION2, self.repairmen_resource, PROC_TYPE_INIT_CS, TIME_TO_CHANGE_PROC_TYPE_CS, MEAN_TIME_TO_FAILURE_CS, PROC_TIME_CAP)
        # self.cap3 = Machine(self.env, 3, "cap", CAP_LOCATION3, self.repairmen_resource, PROC_TYPE_INIT_CS, TIME_TO_CHANGE_PROC_TYPE_CS, MEAN_TIME_TO_FAILURE_CS, PROC_TIME_CAP)
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, [self.ring1, self.ring2], "RingStation")
        self.cap_machine_resource = base_elements.MachineResource(self.env, [self.cap1, self.cap2], "CapStation")
        # monitor resources
        #self.base_station_monitor = monitor.MonitorResource(self.env, self.base_station.resource, "pre")
        self.base_station_monitor = monitor.MonitorResource(self.env,self.base_machine_resource.resource,"pre")
        self.ring_station_monitor = monitor.MonitorResource(self.env, self.ring_machine_resource.resource, "pre")
        self.cap_station_monitor = monitor.MonitorResource(self.env, self.cap_machine_resource.resource, "pre")
        self.destination_monitor = monitor.MonitorResource(self.env, self.destination_station.resource, "post")
        self.mover_monitor = monitor.MonitorResource(self.env, self.mover_resource.resource, "pre")
        # prozess id generator
        self.proc_id_gen = self.process_id_generator()



    def start_simulation(self, time):
        """starts simulation"""
        self.env.run(until=time)
        #print(self.base_station_monitor.data)
        #print(self.destination_monitor.data)
        """
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
        print("Überprüfe ob Maschine währenddessen kaputt geht-repaired event wurde getriggerd in restart")
        print(tester.k.__next__()-1)
        print("maschine hat Prozess abgeschlossen")
        print(tester.g.__next__() - 1)
        print("maschine während laufendem Prozess kaputt gegangen, in interruped, rapaired wird gleich getriggerd")
        print(tester.f.__next__() - 1)
        print("maschine während laufendem Prozess kaputt gegangen aber noch vor Events")
        print(tester.h.__next__() - 1)
        print("resource maschine wird nach abschluss des prozesses wieder freigegeben")
        print(tester.j.__next__() - 1)
        """
    def process_id_generator(self):
        # ToDO vielleicht eher in Produkt Klasse machen und jedes Produkt verwaltet seine Prozesse nach einer ID
        i = 0
        while True:
            i += 1
            yield i



class ProductionManager:
    def __init__(self, factory, strategy: strategy.OrderingStrategy, counter, time, mean_stat=None):
        self.factory = factory
        self.strategy = strategy
        self.production_sequence = None
        self.production_sequence_infos = list()
        self.c0_products = list()
        self.c1_products = list()
        self.proc_compl = list()
        self.point_counter = counter
        self.factory.env.process(self.order_done(time, mean_stat))

    def produce_steps_c0(self, product):
        step_base_cap = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                                 outputs=[product.events["proc_del"]],
                                 resources=[self.factory.base_machine_resource, self.factory.mover_resource,
                                            self.factory.cap_machine_resource],
                                priority=3)
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["proc_del"]],
                             outputs=[product.events["proc_completed"]],
                             resources=[self.factory.mover_resource, self.factory.destination_station],
                             priority=1)
        self.proc_compl.append(product.events["proc_completed"])

    def produce_steps_ccx(self, product):
        """manufactures product"""
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab und liefert es zu Ringstation
        step_base_ring = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                            outputs=[product.events["proc_cap"]],
                            resources=[self.factory.base_machine_resource, self.factory.mover_resource, self.factory.ring_machine_resource],
                            priority=4)
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        step_cap = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                           inputs=[product.events["proc_cap"]],
                           outputs=[product.events["proc_del"]],
                           resources=[self.factory.mover_resource, self.factory.cap_machine_resource],
                           priority= 2)
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["proc_del"]],
                             outputs=[product.events["proc_completed"]],
                             resources=[self.factory.mover_resource, self.factory.destination_station],
                             priority= 1)
        self.proc_compl.append(product.events["proc_completed"])

    def order(self, products):
        """
        sorts products according to production sequence
        """
        id_list = list()
        i = 1
        for partial_order in products:
            id_list.append(i)
            i += partial_order[1]
        self.production_sequence = self.strategy.create_ordering(self.factory.env, self.point_counter, products, id_list)
        for product in self.production_sequence:
            self.production_sequence_infos.append(product.product_infos())
        for product in self.production_sequence:
            if product.proc_steps == "cc0":
                self.produce_steps_c0(product)
                self.c0_products.append(product)
            else:
                self.produce_steps_ccx(product)
                self.c1_products.append(product)

    def order_done(self, time, mean_stat):
        yield simpy.AllOf(self.factory.env, [x.event for x in self.proc_compl])
        stat = Stat()
        stat.get_all_data(self.production_sequence)
        stat.get_record()
        mean_stat.stats.append(stat.dataframe)
        mean_stat.check_if_all_data()
        #data = self.factory.destination_monitor.data
        #plot.plot_product_finish(data, time)
        #data1 = self.factory.base_station_monitor.data
        #plot.plot_product_finish(data1, time)
        self.factory.base_station_monitor.log_book("monitor_base_station.txt")
        self.factory.destination_monitor.log_book("monitor_destination.txt")
        self.factory.ring_station_monitor.log_book("monitor_ring_station.txt")
        self.factory.cap_station_monitor.log_book("monitor_cap_station.txt")
        self.factory.mover_monitor.log_book("monitor_mover.txt")
        #print(f"{self.point_counter.counter} achieved at time point {self.factory.env.now}")


class RewardCounter:
    def __init__(self):
        self.counter = 0


def main(order, sim_time, mean_stat=None):
    factory = SmartFactory()
    counter = RewardCounter()
    production_manager = ProductionManager(factory, strategy.ManufactureingAfterTimeLimitStrategy(), counter, time, mean_stat)
    production_manager.order(order)
    factory.start_simulation(sim_time)
    return factory


if __name__ == '__main__':
    num = 1000
    mean_stat = MeanStat(num)
    for i in range(0,num):
        time = 3000
        main([(1, 1, "cc0", PRODUCT_CC0, 1020), (2, 3, "cc1", PRODUCT_CC1, 1020),
              (3, 3, "cc2", PRODUCT_CC2, 1020), (4, 2, "cc3", PRODUCT_CC3, 1020)],time, mean_stat)

    #data = results.destination_monitor.data
    #print(data)
    #plot.plot_product_finish(data,time)

