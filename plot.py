import matplotlib.pyplot as plt

def plot_product_finish(data, time):
    plt.title('TEST')
    plt.xlabel('Zeitschritte')
    plt.ylabel('Anzahl fertiggestellter Produkte')
    processed_steps = list()
    for element in data:
        processed_steps.append(element[0])
    completed_products = list(range(1, len(processed_steps)+1, 1))
    time_limit = data[-1][0]
    plt.axis([0, (time_limit + (0.2 * time_limit)), 0, len(completed_products)])
    plt.plot(processed_steps,completed_products)
    plt.show()


