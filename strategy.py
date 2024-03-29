from abc import ABC, abstractmethod
from product import ProductCC0, ProductCCX
import settings
import random
import itertools
import time as t


class OrderingStrategy(ABC):
    def __init__(self):
        self.production_sequence = list()

    @abstractmethod
    def create_ordering(self, order: list, env, point_counter, just_products=False):
        """Sorts the order description on products according to the respective strategy and creates the products.
         A sorted production sequence of products is returned.
         :param order: list of products which are sorted after a strategy
         :param env: simpy Environment
         :param point_counter: global counter of the achieved points after production
         :param just_products: Some strategies offer to output only the order without initialising the products.
          This makes it easier to see what the strategy is ordering.
         """
        pass


class FIFOManufacturingStrategy(OrderingStrategy):
    """Leaves the products in the order in which they are arranged in the order description."""
    def create_ordering(self, order, env=None, point_counter=None, just_products=False):
        id_generator = 1
        for specification in order:
            if specification["proc_steps"] == "cc0":
                # Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties:)
                self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                id_generator += 1
            else:
                self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                id_generator += 1
        prios = list(range(1, len(self.production_sequence)+1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list


class ManufactureingAfterTimeLimitStrategy(OrderingStrategy):
    """Arranges the products of the order in ascending order of delivery time. """
    def create_ordering(self, order, env=None, point_counter=None, just_products=False):
        order.sort(key=self.taketime)
        id_generator = 1
        for specification in order:
            if specification["proc_steps"] == "cc0":
                # Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                id_generator += 1
            else:
                self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                id_generator += 1
        prios = list(range(1, len(self.production_sequence) + 1))
        zip_list = list(zip(self.production_sequence, prios))
        return zip_list

    def taketime(self, specification):
        # [env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties]
        return specification["time"]


class ManufactureingRewardStrategy(OrderingStrategy):
    """
    Orders the products according to the highest potential reward that can be obtained if the delivery time can be met.
    A higher reward is preferred over a lower one.
    """
    def create_ordering(self, order, env=None, point_counter=None, just_products=False):
        order.sort(key=self.takepoints, reverse=True)
        id_generator = 1
        if just_products is True:
            return order
        for specification in order:
            if specification["proc_steps"] == "cc0":
                # Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
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
    The order of the products are arranged randomly
    """
    # ToDO: ID ist nach shuffle wieder vertauscht..also ergibt blöde Statistik, muss noch angepasst werden geht nicht
    def create_ordering(self, env, point_counter, order: list, just_products=False):
        id_generator = 1
        for specification in order:
            if specification["proc_steps"] == "cc0":
                # Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties:)
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
    """
    The strategy pursues the goal of arranging the products in such a way that the neighboring products in the
    production sequence are as similar as possible in order to shorten the setup of machines. Here, all products
    are first compared with each other and a scoring is calculated for each product pair. Points are awarded for
    identical component colors. Then a sequence is searched for that achieves the highest possible sum of the scoring
    of the product pairs. For small orders of up to 11 products, all permutations are tried out. For larger ones,
    random arrangements are tried for a fixed time and the one with the best scoring is selected after the time has
    elapsed.
    """
    def create_ordering(self, order: list, env=None, point_counter=None, just_products=False):
        sim_list = []
        for element in order:
            if element not in sim_list:
                sim_list.append(element)
        zip_counter = []
        for element in sim_list:
            zip_counter.append([0, element])
        for k in order:
            for z in zip_counter:
                if z[1] == k:
                    z[0] += 1

        safe_kicked_from_dict = {}
        for element1 in zip_counter:
            for element2 in zip_counter:
                if element1 != element2:
                    if "ring" in element1[1] and "ring" in element2[1]:
                        a = set(element1[1]["ring"])
                        b = set(element2[1]["ring"])
                        if len(a) == len(b):
                            intersect = a.intersection(b)
                            if len(intersect) == len(a):
                                if element1[1]["cap"] == element2[1]["cap"]:
                                    if str(element1[1]) in safe_kicked_from_dict:
                                        safe_kicked_from_dict[str(element1[1])].append(element2)
                                    else:
                                        safe_kicked_from_dict[str(element1[1])] = [element2]
                    elif "ring" not in element1[1] and "ring" not in element2[1]:
                        if element1[1]["cap"] == element2[1]["cap"]:
                            if str(element1[1]) in safe_kicked_from_dict:
                                safe_kicked_from_dict[str(element1[1])].append(element2)
                            else:
                                safe_kicked_from_dict[str(element1[1])] = [element2]
        for key in safe_kicked_from_dict:
            for element in zip_counter:
                if str(element[1]) == key:
                    for config in safe_kicked_from_dict[key]:
                        zip_counter.remove(config)
                        sim_list.remove(config[1])
        zip_list = list(range(1, len(sim_list)+1))
        zipp = list(zip(zip_list, sim_list))
        sim_lst = dict()
        for elem1 in zipp:
            for elem2 in zipp:
                if elem1 != elem2:
                    i = 0
                    a = elem1[1]
                    b = elem2[1]
                    if a["base"] == b["base"]:
                        # null if only spender
                        i += 0
                    if "ring" in a and "ring" in b:
                        ring_colors_a = set(a["ring"])
                        ring_colors_b = set(b["ring"])
                        intersect = ring_colors_a.intersection(ring_colors_b)
                        i += len(intersect)
                    if a["cap"] == b["cap"]:
                        i += 1
                    sim_lst[(elem1[0], elem2[0])] = i
        long_zip = False
        if len(zip_list) > 12:
            long_zip = True
        best_permu = list()
        best_scoring = 0
        if long_zip is True:
            stop = t.time() + 60*5
            while t.time() < stop:
                perm = random.sample(range(1, len(zip_list)+1), len(zip_list))
                counter = 0
                first = 0
                second = 1
                while second < len(perm):
                    counter += sim_lst[(perm[first], perm[second])]
                    first += 1
                    second += 1
                if counter > best_scoring:
                    best_permu = perm
                    best_scoring = counter
        else:
            permutations = itertools.permutations(zip_list)
            while True:
                try:
                    perm = permutations.__next__()
                    counter = 0
                    first = 0
                    second = 1
                    while second < len(perm):
                        counter += sim_lst[(perm[first], perm[second])]
                        first += 1
                        second += 1
                    if counter > best_scoring:
                        best_permu = perm
                        best_scoring = counter
                except StopIteration:
                    break
        new_ordering = list(zip(sim_list, best_permu))
        new_ordering.sort(key=self.get_key)
        a = list(zip(*new_ordering))
        listt = list(a[0])
        end_ordering = []
        for element in listt:
            for e in zip_counter:
                if element == e[1]:
                    for i in range(0, e[0]):
                        end_ordering.append(element)
                    for key in safe_kicked_from_dict:
                        if str(e[1]) == key:
                            for config in safe_kicked_from_dict[key]:
                                for i in range(0, config[0]):
                                    end_ordering.append(config[1])
        if just_products is True:
            return end_ordering
        else:
            id_generator = 1
            for specification in end_ordering:
                if specification["proc_steps"] == "cc0":
                    # Product(env: simpy.Environment, id: int, proc_steps, time_limit_completion, counter, properties: )
                    self.production_sequence.append(ProductCC0(env, id_generator, point_counter, specification))
                    id_generator += 1
                else:
                    self.production_sequence.append(ProductCCX(env, id_generator, point_counter, specification))
                    id_generator += 1
            prios = list(range(1, len(self.production_sequence) + 1))
            zip_list = list(zip(self.production_sequence, prios))
        return zip_list

    def get_key(self, item):
        return item[1]


class StrategySolutionGenerator:
    def __init__(self, number_of_runs):
        self.number_of_runs = number_of_runs
        self.counter = 0
        self.index = 0
        self.sorted_orders = []

    def generate_order_strategy(self):
        order = self.sorted_orders[self.index]
        self.counter += 1
        if self.counter == self.number_of_runs:
            self.index += 1
            self.counter = 0
        return order


if __name__ == '__main__':
    sim = ManufacturingAccordingToSimilarity()
    d = sim.create_ordering(settings.AUSWERTUNG_180[3], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(d)
    print(d)
    e = sim.create_ordering(settings.AUSWERTUNG_180[4], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(e)
    print(e)
    f = sim.create_ordering(settings.AUSWERTUNG_180[5], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(f)
    print(f)
    g = sim.create_ordering(settings.AUSWERTUNG_180[6], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(g)
    print(g)
    h = sim.create_ordering(settings.AUSWERTUNG_180[7], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(h)
    print(h)
    i = sim.create_ordering(settings.AUSWERTUNG_180[8], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(i)
    print(i)
    m = sim.create_ordering(settings.AUSWERTUNG_180[9], just_products=True)
    settings.AUSWERTUNG_180_SIM_SORTED.append(m)
    print(m)
