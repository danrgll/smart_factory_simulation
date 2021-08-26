from sim_robocup import Factory, ProductionManager
import settings

def test_factory(simulation_time, order):
    """
    >>> proc_manager = test_factory(400, [("c1", 6, settings.PRODUCT_C1)])
    >>> observation = list()
    >>> for element in proc_manager.product_list:
    ...     observation.append(len(element.monitor.data))
    >>> observation == [4]*6
    True

    >>> proc_manager = test_factory(1000, [("c1", 20, settings.PRODUCT_C1)])
    >>> observation = list()
    >>> for element in proc_manager.product_list:
    ...     observation.append(len(element.monitor.data))
    >>> observation == [4]*20
    True

    >>> proc_manager = test_factory(100000, [("c1", 2000, settings.PRODUCT_C1)])
    >>> observation = list()
    >>> for element in proc_manager.product_list:
    ...     observation.append(len(element.monitor.data))
    >>> observation == [4]*2000
    True
    """
    factory = Factory()
    production_manager = ProductionManager(factory)
    production_manager.order(order)
    factory.start_simulation(simulation_time)
    return production_manager

