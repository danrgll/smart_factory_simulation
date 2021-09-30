import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Stat:
    def __init__(self):
        self.raw_data = []
        self.modified_data = {'Produkt ID': list(),'Produktionszeitlimit': list(), 'Zeitpunkt der Fertigstellung': list(),
                              'Limit eingehalten': list(), 'mögliche Punkte': list(), 'Punkte erhalten': list(),
                              'Produkttyp': list()}
        self.file_name_generator = FileNameGenerator()
        self.dataframe = None

    def get_all_data(self, product_sequence):
        for product in product_sequence:
            new_data = []
            new_data.append(product.id)
            new_data.append(product.time_limit_of_completion) #timelimit
            new_data.append(product.monitor.data[-1]) # processed time
            if (float(product.time_limit_of_completion) - float(product.monitor.data[-1])) >= 0:
                new_data.append('Ja')
            else:
                new_data.append('Nein')
            new_data.append(product.properties["points"])
            if new_data[3] == 'Ja':
                new_data.append(product.properties["points"])
            else:
                new_data.append(0)
            new_data.append(product.proc_steps)
            self.raw_data.append(new_data)

    def get_record(self):
        for product_data in self.raw_data:
            self.modified_data['Produkt ID'].append(product_data[0])
            self.modified_data['Produktionszeitlimit'].append(product_data[1])
            self.modified_data['Zeitpunkt der Fertigstellung'].append(product_data[2])
            self.modified_data['Limit eingehalten'].append(product_data[3])
            self.modified_data['mögliche Punkte'].append(product_data[4])
            self.modified_data['Punkte erhalten'].append(product_data[5])
            self.modified_data['Produkttyp'].append(product_data[6])
        self.dataframe = pd.DataFrame(self.modified_data, index=self.modified_data['Produkt ID'])

class FileNameGenerator:
    def __init__(self):
        self.i = 0
    def generateName(self):
        name = f"sim{str(self.i)}.pkl"
        self.i += 1
        print(self.i)
        return name

class MeanStat:
    def __init__(self, num):
        self.stats = list()
        self.modified_data = {'Produkt ID': list(),'Produktionszeitlimit': list(), 'Zeitpunkt der Fertigstellung': list(),
                              'Limit eingehalten': list(), 'mögliche Punkte': list(), 'Punkte erhalten': list(),
                              'Produkttyp': list()}
        self.mean_value = []
        self.num = num
        self.df_mean = None
        self.stat_counter = 0

    def check_if_all_data(self):
        self.stat_counter +=1
        print(f"wb{self.stat_counter}")
        if self.stat_counter == self.num:
            self.get_mean_stat()
            self.get_points_final_time()


    def get_mean_stat(self):
        # kriege durchschnitt von den Dataframes irg wie
        df_concat = pd.concat(self.stats)
        print(len(self.stats))
        group_by_row_index = df_concat.groupby(df_concat.index)
        self.df_mean = group_by_row_index.mean()
        print(self.df_mean)
        self.df_mean.plot(x='Zeitpunkt der Fertigstellung', y='Produkt ID', kind = 'scatter')
        plt.show()

    def get_points_final_time(self):
        points_y = list()
        time_x = list()
        for element in self.stats:
            points_y.append(element['Punkte erhalten'].sum())
            time_x.append(element['Zeitpunkt der Fertigstellung'].max())
        plt.ylim(0,self.stats[0]['mögliche Punkte'].sum())
        print(self.stats[0]['mögliche Punkte'].sum())
        plt.title('TEst')
        plt.xlabel('Fertig mit Produktion')
        plt.ylabel('Punkte')
        plt.scatter(time_x,points_y)
        plt.show()

















