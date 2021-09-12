from sim_robocup import Factory, ProductionManager, RewardCounter, main
import settings
import strategy
import unittest

def test_factory(simulation_time, order):
    """
    >>> proc_manager = test_factory(6000, [(1, 6, "ccx", settings.PRODUCT_CC1,500)])
    >>> observation_c0 = list()
    >>> observation_c1 = list()
    >>> for element in proc_manager.c1_products:
    ...     observation_c1.append(len(element.monitor.data))
    >>> observation_c1 == [4]*6
    True

    >>> proc_manager = test_factory(13000, [(1, 20, "ccx", settings.PRODUCT_CC1,1000)])
    >>> observation_c0 = list()
    >>> observation_c1 = list()
    >>> for element in proc_manager.c1_products:
    ...     observation_c1.append(len(element.monitor.data))
    >>> observation_c1 == [4]*20
    True

    >>> proc_manager = test_factory(120000, [(1, 200, "ccx", settings.PRODUCT_CC1,10000)])
    >>> observation_c0 = list()
    >>> observation_c1 = list()
    >>> for element in proc_manager.c1_products:
    ...     observation_c1.append(len(element.monitor.data))
    >>> observation_c1 == [4]*200
    True

    >>> proc_manager = test_factory(150000, [(1, 200, "ccx", settings.PRODUCT_CC1,10000), (2, 10, "cc0", settings.PRODUCT_CC0,10000)])
    >>> observation_c0 = list()
    >>> observation_c1 = list()
    >>> for element in proc_manager.c1_products:
    ...     observation_c1.append(len(element.monitor.data))
    >>> for element in proc_manager.c0_products:
    ...     observation_c0.append(len(element.monitor.data))
    >>> observation_c1 == [4]*200 and observation_c0 == [3]*10
    True
    """
    factory = Factory()
    counter = RewardCounter()
    production_manager = ProductionManager(factory, strategy.FIFOManufacturingStrategy(), counter)
    production_manager.order(order)
    factory.start_simulation(simulation_time)
    return production_manager
"""

class Robocup_Test(unittest.TestCase):

    def test_settings(self):

        self.assertEqual(main([(6, "c1", settings.PRODUCT_C1, 500)],40000))

"""

if __name__ == "__main__":
    import doctest
    print = lambda *args, **kwargs: None
    doctest.testmod()