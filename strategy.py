from abc import ABC, abstractmethod
from product import ProductCC0, ProductCCX
import settings
import random
import itertools
import gc
import multiprocessing as mp


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
    def create_ordering(self, env, point_counter, order: list):
        pass


class FIFOManufacturingStrategy(OrderingStrategy):
    def create_ordering(self, env, point_counter, order):
        id_generator = 1
        for specification in order:
            if specification["proc_steps"] == "cc0":
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
            else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
        prios = list(range(1,len(self.production_sequence)+1))
        zip_list = list(zip(self.production_sequence, prios))
        print(zip_list)
        return zip_list


class ManufactureingAfterTimeLimitStrategy(OrderingStrategy):
    def create_ordering(self, env, point_counter, order):
        order.sort(key=self.taketime)
        id_generator = 1
        print(order)
        for specification in order:
            if specification["proc_steps"] == "cc0":
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
            else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        print(zip_list)
        return zip_list

    def taketime(self, specification):
        # [env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties]
        return specification["time"]


class ManufactureingRewardStrategy(OrderingStrategy):
    """
    products with high points first, then products with lower points follow
    """
    def create_ordering(self, env, point_counter, order):
        order.sort(key=self.takepoints, reverse=True)
        id_generator = 1
        print(order)
        for specification in order:
            if specification["proc_steps"] == "cc0":
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
            else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

    def takepoints(self, specification):
        return specification["points"]


class RandomOrderStrategy(OrderingStrategy):
    """
    Random ordering
    """
    #ToDO: ID ist nach shuffle wieder vertauscht..also ergibt blöde Statistik
    def create_ordering(self, env, point_counter, order: list):
        id_generator = 1
        for specification in order:
            if specification["proc_steps"] == "cc0":
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
            else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
        random.shuffle(self.production_sequence)
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

class ManufacturingAccordingToSimilarity(OrderingStrategy):
    # ToDO: Sortieren nach ähnlichketen, pro Ähnlichkeit, Base Farbe, Ring Farbe, cap etc gibt es einen Punkt
    def create_ordering(self, env, point_counter, order: list):
        sim_list = []
        for element in order:
            if element not in sim_list:
                sim_list.append(element)
        zip_counter = []
        for element in sim_list:
            zip_counter.append([0,element])
        for k in order:
            for z in zip_counter:
                if z[1] == k:
                    z[0] += 1
        zip_list = list(range(1, len(sim_list)+1))
        zipp = list(zip(zip_list,sim_list))
        sim_lst = dict()
        for elem1 in zipp:
            for elem2 in zipp:
                if elem1 != elem2:
                    i = 0
                    a = elem1[1]
                    b = elem2[1]
                    if a["base"] == b["base"]:
                        #null if only spender
                        i += 0
                    if "ring" in a and "ring" in b:
                        #c = min(len(a["ring"]), len(b["ring"]))
                        ring_colors_a = set(a["ring"])
                        ring_colors_b = set(b["ring"])
                        intersect = ring_colors_a.intersection(ring_colors_b)
                        i += len(intersect)
                    if a["cap"] == b["cap"]:
                        i += 1
                    sim_lst[(elem1[0], elem2[0])] = i
        permutations = itertools.permutations(zip_list)
        best_permu = list()
        best_scoring = 0
        while True:
            try:
                perm = permutations.__next__()
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
            except StopIteration:
                break
        new_ordering = list(zip(sim_list,best_permu))
        new_ordering.sort(key=self.get_key)
        a = list(zip(*new_ordering))
        listt = list(a[0])
        end_ordering = []
        for element in listt:
            for e in zip_counter:
                if element == e[1]:
                    for i in range(0,e[0]):
                        end_ordering.append(element)
        print("end list")
        print(end_ordering)
        print(len(end_ordering))
        print(len(listt))
        print(listt)
        id_generator = 1
        for specification in end_ordering:
            if specification["proc_steps"] == "cc0":
                    #Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
            else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        print("hallo")
        print(zip_list)
        return zip_list


    def get_key(self,item):
        return item[1]






























