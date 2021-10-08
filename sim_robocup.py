import base_elements
from base_elements import Event, Process, Resource
import monitor
from repairman import Repairman
from machine import Machine
from mover import Mover
import simpy
from settings import *
import strategy
import plot
import random
from statistic import Stat, FileNameGenerator,MeanStat, MeanMeanStat


class SmartFactory:
    """create amount of resources(machines)"""
    def __init__(self, n_mover, n_base, n_ring, n_cap, n_repairman, des):
        # initialize enviroment
        self.env = simpy.Environment()
        # initialize basic resources
        self.destination_station = Resource(self.env,"del", DEL_LOCATION, des, PROC_TIME_DEL)
        self.repair_mans = list()
        self.movers = list()
        self.base_stations = list()
        self.ring_stations = list()
        self.cap_stations = list()
        # initialize repairman
        for i in range(0,n_repairman):
            self.repair_mans.append(Repairman(self.env, REPAIRMEN_LOCATION, REPAIR_TIME))
        # group repairmen
        self.repairmen_resource = base_elements.RepairmenResource(self.env,self.repair_mans)
        # initialize base
        for i in range(0,n_base):
            self.base_stations.append(Machine(self.env, i, "base", BASE_LOCATION[i], self.repairmen_resource, PROC_TYPE_INIT_BS.copy(), TIME_TO_CHANGE_PROC_TYPE_BS, 1/1000, PROC_TIME_BASE))
        self.base_machine_resource = base_elements.MachineResource(self.env,self.base_stations,"BaseStation")
        # initialize mover
        for i in range(0, n_mover):
            self.movers.append(Mover(self.env,i, MOVER_LOCATION[i], TIME_TO_PICK_UP))
        # group movers
        self.mover_resource = base_elements.MoverResource(self.env,self.movers)
        # initialize machines
        for i in range(0,n_ring):
            self.ring_stations.append(Machine(self.env, i, "ring", RING_LOCATION[i], self.repairmen_resource, PROC_TYPE_INIT_RS.copy(), TIME_TO_CHANGE_PROC_TYPE_RS, 1/1000, PROC_TIME_RING))
        for i in range(0, n_cap):
            self.cap_stations.append(Machine(self.env, i, "cap", CAP_LOCATION[i], self.repairmen_resource, PROC_TYPE_INIT_CS.copy(), TIME_TO_CHANGE_PROC_TYPE_CS, 1/1000, PROC_TIME_CAP))
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, self.ring_stations, "RingStation")
        self.cap_machine_resource = base_elements.MachineResource(self.env, self.cap_stations, "CapStation")
        # monitor resources
        self.base_station_monitor = monitor.MonitorResource(self.env,self.base_machine_resource.resource,"pre")
        self.ring_station_monitor = monitor.MonitorResource(self.env, self.ring_machine_resource.resource, "pre")
        self.cap_station_monitor = monitor.MonitorResource(self.env, self.cap_machine_resource.resource, "pre")
        self.destination_monitor = monitor.MonitorResource(self.env, self.destination_station.resource, "post")
        self.mover_monitor = monitor.MonitorResource(self.env, self.mover_resource.resource, "pre")
        # prozess id generator
        self.proc_id_gen = self.process_id_generator()

    def start_simulation(self):
        """starts simulation"""
        self.env.run()

    def process_id_generator(self):
        i = 0
        while True:
            i += 1
            yield i


class ProductionPlanner:
    def __init__(self, factory, strategy: strategy.OrderingStrategy, counter, mean_stat=None):
        self.factory = factory
        self.strategy = strategy
        self.production_sequence = None
        self.production_sequence_infos = list()
        self.c0_products = list()
        self.c1_products = list()
        self.proc_compl = list()
        self.point_counter = counter
        self.factory.env.process(self.order_done(mean_stat))

    def produce_steps_c0(self, product, prio):
        step_base_cap = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                                 outputs=[product.events["proc_del"]],
                                 resources=[self.factory.base_machine_resource, self.factory.mover_resource,
                                            self.factory.cap_machine_resource],
                                priority=prio)
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["proc_del"]],
                             outputs=[product.events["proc_completed"]],
                             resources=[self.factory.mover_resource, self.factory.destination_station],
                             priority=prio)
        product.processes[step_base_cap.process_id] = step_base_cap
        product.processes[step_final.process_id] = step_final
        self.proc_compl.append(product.events["proc_completed"])

    def produce_steps_ccx(self, product, prio):
        """manufactures product"""
        # ToDo: Monitor Processes
        # Mover fährt zu BaseStation und holt BaseElement ab und liefert es zu Ringstation
        step_base_ring = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                            outputs=[product.events["proc_cap"]],
                            resources=[self.factory.base_machine_resource, self.factory.mover_resource, self.factory.ring_machine_resource],
                            priority=prio)
        # Anfrage an Mover abholen um zu cap zugelangen, fährt zur Cap_station und läd dort Product ab
        step_cap = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                           inputs=[product.events["proc_cap"]],
                           outputs=[product.events["proc_del"]],
                           resources=[self.factory.mover_resource, self.factory.cap_machine_resource],
                           priority= prio)
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["proc_del"]],
                             outputs=[product.events["proc_completed"]],
                             resources=[self.factory.mover_resource, self.factory.destination_station],
                             priority= prio)
        product.processes[step_base_ring.process_id] = step_base_ring
        product.processes[step_cap.process_id] = step_cap
        product.processes[step_final.process_id] = step_final
        self.proc_compl.append(product.events["proc_completed"])

    def order(self, products):
        """
        sorts products according to production sequence
        """
        self.production_sequence = self.strategy.create_ordering(products,self.factory.env, self.point_counter)
        for product in self.production_sequence:
            self.production_sequence_infos.append(product[0].product_infos())
        print(self.production_sequence_infos)
        print(self.production_sequence)
        for (product, prio) in self.production_sequence:
            if product.proc_steps == "cc0":
                self.produce_steps_c0(product, prio)
                self.c0_products.append(product)
            else:
                self.produce_steps_ccx(product,prio)
                self.c1_products.append(product)
        a = list(zip(*self.production_sequence))
        self.production_sequence = list(a[0])
        print(self.production_sequence)
        print(f"after seq {self.proc_compl}")
        self.factory.start_simulation()

    def order_done(self, mean_stat):
        print(f"order_done {self.proc_compl}")
        yield simpy.AllOf(self.factory.env, [x.event for x in self.proc_compl]) or self.factory.env.now
        for machine in self.factory.base_stations:
            machine.end()
        for machine in self.factory.ring_stations:
            machine.end()
        for machine in self.factory.cap_stations:
            machine.end()
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


class RewardCounter:
    def __init__(self):
        self.counter = 0


def main(order, mean_stat=None, mover=6, base=2, ring=4, cap=4, repair=2, des=2):
    #(3,1,2,2,1,1)
    factory = SmartFactory(mover, base, ring, cap, repair, des)
    counter = RewardCounter()
    production_manager = ProductionPlanner(factory, strategy.ManufactureingRewardStrategy(), counter, mean_stat)
    production_manager.order(order)


if __name__ == '__main__':
    file = open("log_all.txt", "w")
    file.write(f"LOG OF FACTORY: \n")
    file.close()
    num = 1000
    mean_mean_stat = MeanMeanStat()
    safe_mean_stat = []
    # 1020 = 17min game time
    # 9 Produkte bei Robocup
        #(2, 1, "cc0", PRODUCT_CC0_2, 6010)]
    for order in AUSWERTUNG_18:
        mean_stat = MeanStat(num)
        for i in range(0, num):
            main(order, mean_stat=mean_stat)
        safe_mean_stat.append(mean_stat)
    for element in safe_mean_stat:
        mean_mean_stat.stats.append(element.df_mean)
        mean_mean_stat.mean_time.extend(element.mean_time)
        mean_mean_stat.mean_points.extend(element.mean_points)
        mean_mean_stat.points_y.extend(element.points_y)
        mean_mean_stat.time_x.extend(element.time_x)
    print(mean_mean_stat.stats)
    print(mean_mean_stat.df_mean)
    print(mean_mean_stat.mean_time)
    print(mean_mean_stat.mean_points)
    mean_mean_stat.get_mean_stat(True)
    mean_mean_stat.plot_mean_points_over_set()
    mean_mean_stat.plot_all_time_points()



