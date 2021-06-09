import simpy

class tasks:
    def __init__(self, product_a, product_b, product_c):
        self.number_of_a = product_a
        self.number_of_b = product_b
        self.number_of_c = product_c

    def prozess_product_a(self, env):
        #löst Prozesse aus
