from abc import ABC, abstractmethod
from product import ProductCC0, ProductCCX
import settings
import random
import itertools

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
                    id_generator += 1
        prios = list(range(1,len(self.production_sequence)+1))
        zip_list = list(zip(self.production_sequence, prios))
        print(zip_list)
        return zip_list


class ManufactureingAfterTimeLimitStrategy(OrderingStrategy):
    def create_ordering(self, env, point_counter, order, id_list):
        order.sort(key=self.taketime)
        print(order)
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
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

    def taketime(self, specification):
        # [env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties]
        return specification[4]


class ManufactureingRewardStrategy(OrderingStrategy):
    """
    products with high points first, then products with lower points follow
    """
    def create_ordering(self, env, point_counter, order, id_list):
        order.sort(key=self.takepoints, reverse=True)
        print(order)
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
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

    def takepoints(self, specification):
        return specification[3]["points"]


class RandomOrderStrategy(OrderingStrategy):
    """
    Random ordering
    """
    #ToDO: ID ist nach shuffle wieder vertauscht..also ergibt blöde Statistik
    def create_ordering(self, env, point_counter, order: list, id_list):
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
                    id_generator += 1
        random.shuffle(self.production_sequence)
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

class ManufacturingAccordingToSimilarity(OrderingStrategy):
    # ToDO: Sortieren nach ähnlichketen, pro Ähnlichkeit, Base Farbe, Ring Farbe, cap etc gibt es einen Punkt
    def create_ordering(self, env, point_counter, order: list, id_list):
        sim_lst = dict()
        for elem1 in order:
            for elem2 in order:
                if elem1[0] != elem2[0]:
                    i = 0
                    a = elem1[3]
                    b= elem2[3]
                    if a["base"] == b["base"]:
                        i += 1
                    if "ring" in a and "ring" in b:
                        #c = min(len(a["ring"]), len(b["ring"]))
                        ring_colors_a = set(a["ring"])
                        ring_colors_b = set(b["ring"])
                        intersect = ring_colors_a.intersection(ring_colors_b)
                        i += len(intersect)
                    if a["cap"] == b["cap"]:
                        i += 1
                    sim_lst[(elem1[0], elem2[0])] = i
        permutations = list(itertools.permutations(list(range(1,len(order)+1))))
        best_permu = list()
        best_scoring = 0
        for perm in permutations:
            counter = 0
            first = 0
            second = 1
            while second < len(perm):
                counter += sim_lst[(perm[first],perm[second])]
                first += 1
                second += 1
            if counter > best_scoring:
                best_permu = perm
                best_scoring = counter
        new_ordering = list(zip(order,best_permu))
        new_ordering.sort(key=self.get_key)
        a = list(zip(*new_ordering))
        listt = list(a[0])
        print(listt)
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
                    id_generator += 1
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list


    def get_key(self,item):
        return item[1]






























