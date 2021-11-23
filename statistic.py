import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import savings


class Stat:
    def __init__(self):
        self.raw_data = []
        self.modified_data = {'Produkt ID': list(), 'Produktionszeitlimit': list(), 'Zeitpunkt der Auslieferung': list(),
                              'Limit eingehalten': list(), 'mögliche Punkte': list(), 'Punkte erhalten': list(),
                              'Produkttyp': list()}
        self.file_name_generator = FileNameGenerator()
        self.dataframe = None

    def get_all_data(self, product_sequence):
        """Stores and evaluates data such as score achieved, whether the delivery time was met, etc. of each product."""
        for product in product_sequence:
            new_data = list()
            new_data.append(product.id)
            new_data.append(product.time_limit_of_completion)  # timelimit
            new_data.append(product.monitor.data[-1])  # processed time
            if (float(product.time_limit_of_completion) - float(product.monitor.data[-1])) >= 0:
                new_data.append('Ja')
            else:
                new_data.append('Nein')
            new_data.append(product.properties["points"])
            if new_data[3] == 'Ja':
                new_data.append(product.properties["points"])
            elif abs(float(product.time_limit_of_completion) - float(product.monitor.data[-1])) <= 10:
                x_80 = (product.properties["points"]*80)/100
                new_data.append(x_80)
            elif abs(float(product.time_limit_of_completion) - float(product.monitor.data[-1])) <= 20:
                x_10 = (product.properties["points"]*10)/100
                new_data.append(x_10)
            else:
                new_data.append(0)
            new_data.append(product.proc_steps)
            self.raw_data.append(new_data)

    def get_record(self):
        """Divides the data of individual products into categories and stores them in these categories. To then
        combine them into one dataframe"""
        for product_data in self.raw_data:
            self.modified_data['Produkt ID'].append(product_data[0])
            self.modified_data['Produktionszeitlimit'].append(product_data[1])
            self.modified_data['Zeitpunkt der Auslieferung'].append(product_data[2])
            self.modified_data['Limit eingehalten'].append(product_data[3])
            self.modified_data['mögliche Punkte'].append(product_data[4])
            self.modified_data['Punkte erhalten'].append(product_data[5])
            self.modified_data['Produkttyp'].append(product_data[6])
        self.dataframe = pd.DataFrame(self.modified_data, index=self.modified_data['Produkt ID'])


class FileNameGenerator:
    def __init__(self):
        self.i = 0

    def generate_name(self):
        name = f"sim{str(self.i)}.pkl"
        self.i += 1
        print(self.i)
        return name


class MeanStat:
    """The data collected by the Stats class(single simulation runs) can be merged and analyzed."""
    def __init__(self, num=None):
        self.stats = list()
        self.modified_data = {'Produkt ID': list(), 'Produktionszeitlimit': list(), 'Zeitpunkt der Auslieferung': list(),
                              'Limit eingehalten': list(), 'mögliche Punkte': list(), 'Punkte erhalten': list(),
                              'Produkttyp': list()}
        self.mean_value = []
        self.num = num
        self.df_mean = None
        self.stat_counter = 0
        self.mean_points = []
        self.mean_time = []
        self.time_x = []
        self.points_y = []

    def check_if_all_data(self):
        """Check whether all simulations have already been run. Merges the collected data of the individual
         simulations and evaluates them"""
        self.stat_counter += 1
        print(f"Durchlauf{self.stat_counter}")
        if self.stat_counter == self.num:
            self.get_mean_stat()
            self.get_points_final_time()
            self.get_mean_point_time()

    def get_mean_stat(self, plot=False):
        """merges the individual data frames into one large one and evaluates the average of all of them as far
          as this is possible via the categories. Optionally, the average times of completion of individual products
          are output graphically """
        df_concat = pd.concat(self.stats)
        print(len(self.stats))
        group_by_row_index = df_concat.groupby(df_concat.index)
        self.df_mean = pd.DataFrame(group_by_row_index.mean())
        print(self.df_mean)
        if plot is True:
            self.df_mean.plot(x='Zeitpunkt der Auslieferung', y='Produkt ID', kind='scatter')
            plt.show()

    def get_points_final_time(self, plot=False):
        """Sums up the achieved points of all products and stores them with the respective end of the production period.
         Optionally, this can be output graphically for all tests."""
        max_over_all = 0
        min_over_all = None
        po_points = self.stats[0]['mögliche Punkte'].sum()
        for element in self.stats:
            p = element['Punkte erhalten'].sum()
            self.points_y.append((p*100)/po_points)
            max = element['Zeitpunkt der Auslieferung'].max()
            self.time_x.append(max)
            if max > max_over_all:
                max_over_all = max
            if min_over_all is None:
                min_over_all = max
            elif min_over_all > max:
                min_over_all = max
        if plot is True:
            plt.xticks(np.arange(0, max_over_all, step=1000))
            plt.ylim(0, self.stats[0]['mögliche Punkte'].sum())
            print(self.stats[0]['mögliche Punkte'].sum())
            plt.title('TEst')
            plt.xlabel('Fertig mit Produktion')
            plt.ylabel('Punkte')
            plt.scatter(self.time_x, self.points_y)
            plt.show()

    def get_mean_point_time(self, plot=False):
        """evaluates the average achieved score in % over all simulations as well as the average time of completion of
         the order. Optionally, these two parameters can be output graphically in relation to each other."""
        counter_points = 0
        counter_time = 0
        points = []
        time = []
        po_points = self.stats[0]['mögliche Punkte'].sum()
        for element in self.stats:
            p = element['Punkte erhalten'].sum()
            points.append((p*100)/po_points)
            time.append(element['Zeitpunkt der Auslieferung'].max())
        for point in points:
            counter_points += point
        for t in time:
            counter_time += t
        self.mean_points.append(counter_points / len(points))
        self.mean_time.append(counter_time / len(time))
        if plot is True:
            plt.title('Test')
            plt.xlabel('Durchschnittlicher Zeitpunkt der Fertigstellung')
            plt.ylabel('Punkte erhalten in %')
            plt.scatter(self.mean_time, self.mean_points)
            plt.show()


class MeanMeanStat:
    """The data collected by the MeanStats class(Data over all Simulations) can be merged and analyzed. In this way,
    the results of orders with the same number of products can be compared."""
    def __init__(self, num=None):
        self.stats = list()
        self.modified_data = {'Produkt ID': list(), 'Produktionszeitlimit': list(), 'Zeitpunkt der Fertigstellung': list(),
                              'Limit eingehalten': list(), 'mögliche Punkte': list(), 'Punkte erhalten': list(),
                              'Produkttyp': list()}
        self.mean_value = []
        self.num = num
        self.df_mean = None
        self.stat_counter = 0
        self.mean_points = []
        self.mean_time = []
        self.time_x = []
        self.points_y = []

    def get_mean_stat(self, plot=False):
        """merges the individual data frames into one large one and evaluates the average of all of them as far
          as this is possible via the categories. Optionally, the average times of completion of individual products
          are output graphically"""
        df_concat = pd.concat(self.stats)
        print(len(self.stats))
        group_by_row_index = df_concat.groupby(df_concat.index)
        self.df_mean = pd.DataFrame(group_by_row_index.mean())
        print(self.df_mean)
        if plot is True:
            self.df_mean.plot(x='Zeitpunkt der Auslieferung', y='Produkt ID', kind='scatter', title='Zeitpunkt der Auslieferung je Produkt')
            plt.show()

    def plot_mean_points_over_set(self):
        """plot the average cycle time and average achieved score per order"""
        plt.title('Durchschnittliche Durchlaufzeit und erreichte Punktzahl pro Auftrag')
        plt.xlabel('Durchschnittliche Durchlaufzeit')
        plt.ylabel('erreichte Punkte in %')
        # plt.axis([xmin, xmax, ymin, ymax])
        plt.axis([0, 3000, 0, 100])
        print("Mean Time")
        print(self.mean_time)
        print("mean_points")
        print(self.mean_points)
        plt.scatter(self.mean_time, self.mean_points, color=['red', 'green', 'blue', 'grey', 'black', 'orange',
                                                             'cyan', 'brown', 'purple', 'lime'])
        plt.show()

    def plot_all_time_points(self):
        """plot all processing times of the orders and the achieved score per simulation."""
        plt.title('Durchlaufzeit und die erreichte Punktzahl aller Simulationen der Aufträge')
        plt.xlabel('Durchlaufzeit')
        plt.ylabel('erreichte Punkte in %')
        plt.axis([0, 3000, 0, 100])
        plt.scatter(self.time_x, self.points_y)
        print("all_times_x")
        print(self.time_x)
        print("all_points_y")
        print(self.points_y)
        plt.show()


def plot_combi_strategy_mean_points(x, y):
    """Graphical comparison of two strategies of the average points achieved."""
    plt.title('')
    plt.xlabel('durchschnittlich erreichte Punkte in %, Time')
    plt.ylabel('durchschnittlich erreichte Punkte in %, Fifo')
    plt.axis([0, 100, 0, 100])
    plt.scatter(x, y, color=['red', 'green', 'blue', 'grey', 'black', 'orange', 'cyan', 'brown', 'purple', 'lime'])
    plt.plot([0, 100], [0, 100], '-', c='black', linewidth=.8)
    plt.show()


def plot_combi_strategy_mean_time(x, y):
    """Graphical comparison of two strategies of average lead time."""
    plt.title('')
    plt.xlabel('durchschnittliche Durchlaufzeit, Time')
    plt.ylabel('durchschnittliche Durchlaufzeit, Fifo')
    plt.axis([0, 2000, 0, 2000])
    plt.scatter(x, y, color=['red', 'green', 'blue', 'grey', 'black', 'orange', 'cyan', 'brown', 'purple', 'lime'])
    plt.plot([0, 1], [0, 10000], '-', c='black', linewidth=.8)
    plt.show()


def boxplot_points_strategy(f, r, t, s):
    """Comparison of the 4 strategies over achieved points of all simulations prepared as boxplot."""
    plt.title('')
    plt.xlabel('Strategien')
    plt.ylabel('erreichte Punkte in % aller Simulationen der Aufträge')
    ax = plt.gca()
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    data = [f, r, t, s]
    plt.boxplot(data)
    plt.xticks([1, 2, 3, 4], ['Fifo', 'Reward', 'Time', 'Similarity'])
    plt.show()


def boxplot_time_strategy(f, r, t, s):
    """Comparison of the 4 strategies over the lead times of all simulations of the orders prepared as boxplot"""
    plt.xlabel('Strategien')
    plt.ylabel('Durchlaufzeiten aller Simulationen der Aufträge')
    ax = plt.gca()
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    data = [f, r, t, s]
    plt.xticks([1, 2, 3, 4], ['Fifo', 'Reward', 'Time', 'Similarity'])
    plt.boxplot(data)
    plt.xticks([1, 2, 3, 4], ['Fifo', 'Reward', 'Time', 'Similarity'])
    plt.show()


def boxplot_components_changes_points(init, rob, base, ring, cap, repair, des):
    """Comparison of the achieved points of all simulations of the orders in case of changes of the individual
    components of the factory with an initial factory."""
    plt.xlabel('Erhöhung der jeweiligen Komponenten um Faktor 2')
    plt.ylabel('erreichte Punkte in % aller Simulationen der Aufträge')
    ax = plt.gca()
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    data = [init, rob, ring, des, base, cap, repair]
    plt.axis([0, 8, 0, 100])
    plt.boxplot(data)
    plt.xticks([1, 2, 3, 4, 5, 6, 7], ['Init', 'Robo', 'Ring', 'Del', 'Base', 'Cap', 'Ins'])
    plt.show()


def boxplot_components_changes_time(init, rob, base, ring, cap, repair, des):
    """Comparison of the lead times of all simulations of the orders with changes of the individual components
    of the factory with an initial factory."""
    plt.xlabel('Erhöhung der jeweiligen Komponenten um Faktor 2')
    plt.ylabel('Durchlaufzeiten aller Simulationen der Aufträge')
    ax = plt.gca()
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    data = [init, rob, ring, des, base, cap, repair]
    plt.boxplot(data)
    plt.xticks([1, 2, 3, 4, 5, 6, 7], ['Init', 'Robo', 'Ring', 'Del', 'Base', 'Cap', 'Ins'])
    plt.show()


if __name__ == '__main__':
    # plot_combi_strategy_mean_points(savings.t1_mean_points, savings.f1_mean_points)
    # plot_combi_strategy_mean_time(savings.t1_mean_time, savings.f1_mean_time)
    # boxplot_points_strategy(savings.f1_all_points, savings.r1_all_points, savings.t1_all_points, savings.s1_all_points)
    # boxplot_time_strategy(savings.f1_all_time, savings.r1_all_time, savings.t1_all_time, savings.s1_all_time)
    boxplot_components_changes_points(savings.re_all_points, savings.robo_all_points, savings.base_all_points,
                                      savings.ring_all_points, savings.cap_all_points, savings.re_all_points,
                                      savings.des_all_points)
    boxplot_components_changes_time(savings.r_all_time, savings.robo_all_time,
                                    savings.base_all_time, savings.ring_all_time, savings.cap_all_time,
                                    savings.re_all_time, savings.des_all_time)
