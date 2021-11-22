import base_elements
from base_elements import Process, Resource
import monitor
from repairman import Repairman
from machine import Machine
from mover import Mover
import simpy
from settings import *
import strategy
from statistic import Stat, MeanStat, MeanMeanStat


class SmartFactory:
    """create a factory with a set of resources, which are then each grouped and given to their resource manager. """
    def __init__(self, n_mover, n_base, n_ring, n_cap, n_repairman, des):
        """
        :param n_mover: number of movers
        :param n_base: number of base stations
        :param n_ring: number of ring stations
        :param n_cap: number of cap stations
        :param n_repairman: number of repairmen
        :param des: number of delivery stations
        """
        # initialize enviroment
        self.env = simpy.Environment()
        # initialize basic resources
        self.destination_station = Resource(self.env, "del", DEL_LOCATION, des, PROC_TIME_DEL)
        # initialize resource manager
        self.repair_mans = list()
        self.movers = list()
        self.base_stations = list()
        self.ring_stations = list()
        self.cap_stations = list()
        # initialize repairman
        for i in range(0, n_repairman):
            self.repair_mans.append(Repairman(self.env, REPAIRMEN_LOCATION, REPAIR_TIME))
        # group repairmen
        self.repairmen_resource = base_elements.RepairmenResource(self.env, self.repair_mans)
        # initialize base
        for i in range(0, n_base):
            self.base_stations.append(Machine(self.env, i, "base", BASE_LOCATION_18[i], self.repairmen_resource,
                                              PROC_TYPE_INIT_BS.copy(), TIME_TO_CHANGE_PROC_TYPE_BS, 1/500,
                                              PROC_TIME_BASE))
        self.base_machine_resource = base_elements.MachineResource(self.env, self.base_stations, "BaseStation")
        # initialize mover
        for i in range(0, n_mover):
            self.movers.append(Mover(self.env, i, MOVER_LOCATION[i], TIME_TO_PICK_UP))
        # group movers
        self.mover_resource = base_elements.MoverResource(self.env, self.movers)
        # initialize machines
        for i in range(0, n_ring):
            self.ring_stations.append(Machine(self.env, i, "ring", RING_LOCATION_18[i], self.repairmen_resource,
                                              PROC_TYPE_INIT_RS.copy(), TIME_TO_CHANGE_PROC_TYPE_RS,
                                              1/500, PROC_TIME_RING))
        for i in range(0, n_cap):
            self.cap_stations.append(Machine(self.env, i, "cap", CAP_LOCATION_18[i], self.repairmen_resource,
                                             PROC_TYPE_INIT_CS.copy(), TIME_TO_CHANGE_PROC_TYPE_CS,
                                             1/500, PROC_TIME_CAP))
        # group machines to resources
        self.ring_machine_resource = base_elements.MachineResource(self.env, self.ring_stations, "RingStation")
        self.cap_machine_resource = base_elements.MachineResource(self.env, self.cap_stations, "CapStation")
        # monitor resources
        self.base_station_monitor = monitor.MonitorResource(self.env, self.base_machine_resource.resource, "pre")
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
        """generate process ids"""
        i = 0
        while True:
            i += 1
            yield i


class ProductionPlanner:
    """The production planner manages and initializes the production of a factory. The planner is given an order
    of products, which are then arranged according to a chosen strategy. For each product, the necessary processes
    for production are initialized. After the order is completed, the machines are shut down and certain statistics
    of the production can be retrieved."""
    def __init__(self, factory, strategy: strategy.OrderingStrategy, counter, mean_stat=None):
        """
        :param factory: Factory in which the production takes place
        :param strategy: Strategy according to which the production sequence is arranged
        :param counter: global counter for point evaluation
        :param mean_stat: Statistics into which the collected data flow and can be graphically evaluated
        """
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
        """initializes the process steps which are necessary for the completion of the product C0.
        :param product
        :param Priority of the product. Between 1 and the number of products
        """
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
        """initializes the process steps which are necessary for the completion of the product C1,C2,C3.
        :param product
        :param Priority of the product. Between 1 and the number of products
        """
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
                           priority=prio)
        # Anfrage an Mover um Produkt an Zieldestination abzugeben
        step_final = Process(self.factory.env, product, self.factory.proc_id_gen.__next__(),
                             inputs=[product.events["proc_del"]],
                             outputs=[product.events["proc_completed"]],
                             resources=[self.factory.mover_resource, self.factory.destination_station],
                             priority=prio)
        product.processes[step_base_ring.process_id] = step_base_ring
        product.processes[step_cap.process_id] = step_cap
        product.processes[step_final.process_id] = step_final
        self.proc_compl.append(product.events["proc_completed"])

    def order(self, products):
        """
        The transferred order of products is arranged according to a strategy and handed over to the factory for
         completion. Then the simulation starts.
        """
        self.production_sequence = self.strategy.create_ordering(products, self.factory.env, self.point_counter)
        for product in self.production_sequence:
            self.production_sequence_infos.append(product[0].product_infos())
        for (product, prio) in self.production_sequence:
            if product.proc_steps == "cc0":
                self.produce_steps_c0(product, prio)
                self.c0_products.append(product)
            else:
                self.produce_steps_ccx(product, prio)
                self.c1_products.append(product)
        a = list(zip(*self.production_sequence))
        self.production_sequence = list(a[0])
        self.factory.start_simulation()

    def order_done(self, mean_stat):
        """After completion of all products, carries out statistics on production and finishes the work of machines.
        Logs of resource managers are also issued. Stops Simulation."""
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
        # commented out in order not to evaluate directly after each simulation
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
    """Serves as a simple counter of the points"""
    def __init__(self):
        self.counter = 0


def main(order, strategy, mean_stat=None, mover=7, base=2, ring=5, cap=4, repair=2, des=4):
    """initialises a factory with a given number of components and a reward counter and production planner to which a
     selected starter is passed. After initialisation, the given order is organised by the production planner
      and produced by the factory.
      :param strategy: The strategy according to which the priority of the production sequence is determined
      :param mean_stat: Statistics in which relevant data are recorded and stored: class Mean_stat
      :param mover: number of movers in the factory
      :param base: number of base stations in the factory
      :param ring: number of ring stations in the factory
      :param cap: number of cap stations in the factory
      :param repair: number of repairmen in the factory
      :param des: number of delivery stations in the factory
      """
    # (3,1,2,2,1,1)
    # (6,2,4,4,2,2)
    # (12,4,8,8,4,4)
    factory = SmartFactory(mover, base, ring, cap, repair, des)
    counter = RewardCounter()
    production_manager = ProductionPlanner(factory, strategy, counter, mean_stat)
    production_manager.order(order)


if __name__ == '__main__':
    file = open("log_all.txt", "w")
    file.write(f"LOG OF FACTORY: \n")
    file.close()
    num = 1000  # number of simulation runs
    mean_mean_stat = MeanMeanStat()  # Data of all orders and their respective average times of all runs.
    safe_mean_stat = []  # Data of all runs of an order
    for order in AUSWERTUNG_18:
        mean_stat = MeanStat(num)
        for i in range(0, num):
            main(order, strategy.ManufactureingAfterTimeLimitStrategy(), mean_stat=mean_stat)  # Simulation of the individual orders
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
    # Evaluation of the statistics
    mean_mean_stat.get_mean_stat(True)
    mean_mean_stat.plot_mean_points_over_set()
    mean_mean_stat.plot_all_time_points()
