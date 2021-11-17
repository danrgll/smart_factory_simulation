import itertools
import random


def generate_all_possible_dics(colors_base: list, colors_ring: list, colors_cap: list, start: int, end: int):
    """Generate all possible product types with the different colours of the individual elements. Choose as many of the
     4 product types from the universe of all possibilities that all exist in equal numbers and output them."""
    result = list()
    c_1 = list()
    c_2 = list()
    c_3 = list()
    for c1 in colors_base:
        for c2 in colors_cap:
            dic = {"proc_steps": "cc0", "base": [c1], "cap": [c2], "points": 15, "time": random.randint(start, end)}
            result.append(dic)
            for c3 in colors_ring:
                dic = {"proc_steps": "cc1", "base": [c1], "ring": [c3], "cap": [c2], "points": 25, "time": random.randint(start, end)}
                c_1.append(dic)
            for c3 in itertools.permutations(colors_ring, 2):
                dic = {"proc_steps": "cc2", "base": [c1], "ring": [c for c in c3], "cap": [c2], "points": 45, "time": random.randint(start, end)}
                c_2.append(dic)
            for c3 in itertools.permutations(colors_ring, 3):
                dic = {"proc_steps": "cc3", "base": [c1], "ring": [c for c in c3], "cap": [c2], "points": 75, "time": random.randint(start, end)}
                c_3.append(dic)
    i = len(result)
    for element in random.sample(c_1, i):
        result.append(element)
    for element in random.sample(c_2, i):
        result.append(element)
    for element in random.sample(c_3, i):
        result.append(element)
    return result


def choose_runner_class(possible_dics):
    """The different products are divided into three classes. So-called high runners, mid runners and low runners.
     15% of the products are high runners. 50% mid runners and the rest low runners."""
    result = dict()
    number_high_runner = int(round(len(possible_dics) * 0.15, 0))
    number_mid_runner = int(round(len(possible_dics) * 0.5, 0))
    result["high_runner"] = random.sample(possible_dics, number_high_runner)
    for dic in result["high_runner"]:
        possible_dics.remove(dic)
    result["mid_runner"] = random.sample(possible_dics, number_mid_runner)
    for dic in result["mid_runner"]:
        possible_dics.remove(dic)
    result["low_runner"] = possible_dics
    return result


def generate_products(runner_dic, number_of_products):
    """With the help of the different product classes, a selected number of products are output. This set of products
    consists of 70% highrunners, 25% midrunners and 5% lowrunners. These are randomly selected from the classes and
    can appear several times."""
    result = list()
    number_of_high_runner_products = int(round(number_of_products * 0.7))
    number_of_mid_runner_products = int(round(number_of_products * 0.25))
    number_of_low_runner_products = number_of_products - number_of_high_runner_products - number_of_mid_runner_products
    for i in random.choices(runner_dic["high_runner"], k=number_of_high_runner_products):
        result.append(i)
    for i in random.choices(runner_dic["mid_runner"], k=number_of_mid_runner_products):
        result.append(i)
    for i in random.choices(runner_dic["low_runner"], k=number_of_low_runner_products):
        result.append(i)
    random.shuffle(result)
    return result


if __name__ == "__main__":
    a = ["Black", "Red", "Grey"]  # colors base
    b = ["Black", "Grey"]  # colors cap
    c = ["Blue", "Red", "Green", "Orange", "Yellow"]  # colors ring
    d = generate_all_possible_dics(a, c, b, 700, 10200)
    r = choose_runner_class(d)
    p = generate_products(r, 180)
    print(p)
    print(len(p))
