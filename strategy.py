from abc import ABC, abstractmethod
from product import ProductCC0, ProductCCX
import settings

"""
def product_id_generator():
    # ToDO vielleicht eher in Produkt Klasse machen und jedes Produkt verwaltet seine Prozesse nach einer ID
    i = 0
    while True:
        i += 1
        yield i
"""

class OrderingStrategy(ABC):
    def __init__(self):
        self.production_sequence = list()

    @abstractmethod
    def create_ordering(self, env, point_counter, order: list, id_list):
        pass


class FIFOManufacturingStrategy(OrderingStrategy):
    def create_ordering(self, env, point_counter, order, id_list):
        for specification in order:
            id_generator = id_list[specification[0] -1]
            if specification[2] == "cc0":
                for i in range(0,specification[1]):
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    id_generator += 1
            else:
                for i in range(0, specification[1]):
                    self.production_sequence.append(ProductCCX(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    i += 1
        return self.production_sequence


class ManufactureingAfterTimeLimitStrategy(OrderingStrategy):
    def create_ordering(self, env, point_counter, order, id_list):
        order.sort(key=self.taketime)
        for specification in order:
            id_generator = id_list[specification[0] - 1]
            if specification[2] == "cc0":
                for i in range(0,specification[1]):
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    id_generator += 1
            else:
                for i in range(0, specification[1]):
                    self.production_sequence.append(ProductCCX(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    id_generator += 1
        return self.production_sequence

    def taketime(self, specification):
        # [env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties]
        return specification[4]


class ManufactureingRewardStrategy(OrderingStrategy):
    """
    products with high points first, then products with lower points follow
    """
    def create_ordering(self, env, point_counter, order, id_list):
        order.sort(key=self.takepoints, reverse=True)
        for specification in order:
            id_generator = id_list[specification[0] - 1]
            if specification[2] == "cc0":
                for i in range(0, specification[1]):
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    id_generator += 1
            else:
                for i in range(0, specification[1]):
                    self.production_sequence.append(ProductCCX(env, id_generator, specification[2], specification[4], point_counter, specification[3]))
                    id_generator += 1
        return self.production_sequence

    def takepoints(self, specification):
        return specification[3]["points"]

