import itertools
import random

def generate_all_possible_dics(colors_base,colors_ring, colors_cap, start, end):
    result = list()
    c_1 = list()
    c_2 = list()
    c_3 = list()
    for c1 in colors_base:
        for c2 in colors_cap:
            dic = {"proc_steps": "cc0", "base": [c1], "cap": [c2], "points": 5, "time": random.randint(start, end)}
            result.append(dic)
            for c3 in colors_ring:
                dic = {"proc_steps": "cc1", "base": [c1], "ring": [c3], "cap": [c2], "points": 5, "time": random.randint(start, end)}
                c_1.append(dic)
            for c3 in itertools.permutations(colors_ring, 2):
                dic = {"proc_steps": "cc2", "base": [c1], "ring": [c for c in c3], "cap": [c2], "points": 10, "time": random.randint(start, end)}
                c_2.append(dic)
            for c3 in itertools.permutations(colors_ring, 3):
                dic = {"proc_steps": "cc3", "base": [c1], "ring": [c for c in c3], "cap": [c2], "points": 20, "time": random.randint(start, end)}
                c_3.append(dic)
    i = len(result)
    for element in random.sample(c_1,i):
        result.append(element)
    for element in random.sample(c_2,i):
        result.append(element)
    for element in random.sample(c_3, i):
        result.append(element)
    print(len(result))
    return result


def choose_runner_class(possible_dics):
    result = {}
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
    result = []
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


if __name__=="__main__":
    a = ["Black", "Red", "Grey"]
    b = ["Black", "Grey"]
    c = ["Blue", "Red", "Green", "Orange", "Yellow"]
    d = generate_all_possible_dics(a, c, b, 710, 1020)
    r = choose_runner_class(d)
    p = generate_products(r, 18)
    print(p)
    print(len(p))
#d
#Durchlaufzeit
#Termintreue