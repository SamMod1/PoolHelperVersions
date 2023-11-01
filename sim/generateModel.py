import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import warnings
import os


POSITIVES_TO_GEN = (1, 93)  # The range of true positives per plate this analysis should consider
PLATES_TO_GEN = 50000  # How many plates to generate for each number of positives in the range POSITIVES_TO_GEN
PLATE_DIMENSIONS = (8, 12)  # Dimensions for the microplate array. E.g. (8, 12) for 96 well plates, (24, 16) for 384 well plates
CONTROL_POSITIONS = ((8, 10), (8, 11), (8, 12))  # The locations on plates which contain any control wells
CHANNEL_POSITIVITY = 0.4  # Positivity rate for the testing channel of interest
PLATE_SIZE = 96
CONTROL_NUMBER = len(CONTROL_POSITIONS)
random.seed(1)



def add_positives(plate_matrix, num_pos : int): # Black Flake8 MyPy
    """
    Changes a given number of wells in a matrix representing a microplate from negative (zero) to positive (one), 
    based on randomly chosen locations.

    Parameters:
    plate_matrix : Matrix
        A 2D matrix representing a microplate assay, zeros represent negative samples, ones represent positive values.
    
    num_pos : an integer
        The number of randomly placed positives to add to the plate matrix

    Returns:
    Matrix (representing the plate with positives added)
    """
    plate_dimensions = plate_matrix.shape
    plate_matrix = plate_matrix.flatten()
    potential_wells = np.where(plate_matrix == 0)[0].tolist()
    for _ in range(num_pos):
        choice = random.choice(potential_wells)
        plate_matrix[choice] = 1
        potential_wells.remove(choice)
    return np.reshape(plate_matrix, plate_dimensions)


def analyse_plate(plate_matrix):
    """
    Determines the size of every vertical and horiztonal stripe of positives on a microplate

    Parameters:
    plate_matrix : Matrix
        A 2D matrix representing a microplate assay, zeros represent negative samples, ones represent positive values.
        Controls can be represented by any other value
    
    Returns:
    A tuple containing two lists of numbers. The numbers in the first list represent the sizes of each horizontal stripe,
    the second list contains the sizes of each vertical stripe of positves.
    """
    plate_dimensions = plate_matrix.shape
    blank_matrix = np.array([[[0,0] for _ in range(plate_dimensions[1])] for _ in range(plate_dimensions[0])])
    adjacent_positives = []
    hor_group = 0
    hor_groups = []
    ver_group = 0
    ver_groups = []
    for row in range(plate_dimensions[0]):
        for col in range(plate_dimensions[1]):
            if plate_matrix[(row, col)] == 1:
                if not col == plate_dimensions[1] - 1:
                    if plate_matrix[(row, col + 1)] == 1 and blank_matrix[(row, col + 1)][0] == 0:
                        blank_matrix[(row, col)][0] = 1
                        hor_groups.append(1)
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            adjacent_positives.pop(0)
                            if current_well[1] + 1 > plate_dimensions[1] - 1:  # I.e if we hit the end of a row
                                break
                            right_well = (current_well[0], current_well[1] + 1)
                            if plate_matrix[right_well] == 1 and blank_matrix[right_well][0] == 0:
                                blank_matrix[right_well][0] = 1
                                adjacent_positives.append(right_well)
                                hor_groups[hor_group] += 1
                        hor_group += 1
                if not row == plate_dimensions[0] - 1:
                    if plate_matrix[(row + 1, col)] == 1 and blank_matrix[(row + 1, col)][1] == 0:
                        blank_matrix[(row, col)][1] = 1
                        ver_groups.append(1)
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            adjacent_positives.pop(0)
                            if current_well[0] + 1 > plate_dimensions[0] - 1:
                                break
                            well_below = (current_well[0] + 1, current_well[1])
                            if plate_matrix[well_below] == 1 and blank_matrix[well_below][1] == 0:
                                blank_matrix[well_below][1] = 1
                                adjacent_positives.append(well_below)
                                ver_groups[ver_group] += 1
                        ver_group += 1
    return (hor_groups, ver_groups)


def get_stats(plate, n_positives : int):
    plate = add_positives(plate, n_positives)
    return analyse_plate(plate)


class Simulator:
    def __init__(self, plate_dimensions, positives_to_gen, control_pos, plates_to_gen, saved_plates = False):
        self.positives_to_gen = positives_to_gen
        self.plate_dimensions = plate_dimensions
        self.control_pos = control_pos
        self.plates_to_gen = plates_to_gen
        self.df = None
        if not saved_plates:
            self.plates = []
        else:
            self.plates = saved_plates
        self.stats = []

    def simulate(self):
        self.stats = []
        if len(self.plates) == 0:
            for num_pos in range(self.positives_to_gen[0], self.positives_to_gen[1] + 1):
                results = []
                print(num_pos)
                plate = np.array([[0 for _ in range(self.plate_dimensions[1])] for _ in range(self.plate_dimensions[0])])
                for pos in self.control_pos:
                    plate[(pos[0] - 1, pos[1] - 1)] = 2
                self.plates = [plate.copy() for _ in range(self.plates_to_gen)]
                for plate in self.plates:
                    results.append(get_stats(plate, num_pos))
                self.stats.append(list(results))
            self.plates = []
        else:
            pass
    
    def analyse_sim(self):
        positives = []
        max_hor = []
        num_hor_twos = []
        max_vert = []
        num_vert_twos = []
        for num_pos, stats in enumerate(self.stats):
            for plate in stats:
                positives.append(num_pos + 1)
                if len(plate[0]) == 0:
                    max_hor.append(0)
                else:
                    max_hor.append(max(plate[0]))
                num_hor_twos.append(sum([int(x / 2) for x in plate[0]]))
                if len(plate[1]) == 0:
                    max_vert.append(0)
                else:
                    max_vert.append(max(plate[1]))
                num_vert_twos.append(sum([int(x / 2) for x in plate[1]]))
        self.df = pd.DataFrame({'Positives' : positives, 'Max_Horizontal' : max_hor, 'Num_Horizontal_Twos' : num_hor_twos,
                                'Max_Vertical' : max_vert, 'Num_Vertical_Twos' : num_vert_twos})
        self.df.loc[self.df['Max_Horizontal'] == 0, 'Max_Horizontal'] = 1
        self.df.loc[self.df['Max_Vertical'] == 0, 'Max_Vertical'] = 1

    def generate_plot(self, stat: str):
        means = {}
        sd = {}
        for n_pos in self.df['Positives'].unique():
            stripes = self.df.loc[self.df['Positives'] == n_pos, stat]
            means[n_pos] = stripes.mean()
            sd[n_pos] = stripes.std()
        
        labels = list(means.keys())
        values = list(means.values())
        sd = list(sd.values())
        fig = plt.figure(figsize = (12, 8))
        plt.bar(labels, values)
        plt.errorbar(labels, values, yerr = sd, fmt = 'o')
        

    def expected_positivities(self, pos_prev):
        plate_list = []
        if self.plates_to_gen < 1000:
            warnings.warn("Warning: positives_to_gen should be as high as possible, low number will result in low accuracy")
        for sim_plate in range(self.plates_to_gen):
            positives = 0
            for well in range((self.plate_dimensions[0] * self.plate_dimensions[1]) - len(self.control_pos)):
                if random.random() < pos_prev:
                    positives += 1
            plate_list.append(positives)
        plate_list = sorted(plate_list)
        rtn = {
            0.5 : plate_list[int(len(plate_list) / 2)], 
            0.1 : plate_list[int(len(plate_list) * 0.9)], 
            0.05 : plate_list[int(len(plate_list) * 0.95)]
            }
        return rtn

    def _calculate_p(self, num_pos, alpha_value, df_col):
        max_groups = max(self.df.loc[self.df['Positives'] == num_pos][df_col])
        for num_groups in [x + 1 for x in range(24)]:
            p = len(self.df.loc[(self.df['Positives'] == num_pos) & (self.df[df_col] >= num_groups)]) / len(self.df.loc[self.df['Positives'] == num_pos])
            if p == 0:
                return num_groups - 1
            if p < alpha_value:
                return num_groups - 1
            if num_groups == max_groups:
                return num_groups
            
    def _column_p_thresholds(self, df_col, alpha_value):
        intervals = []
        for num_pos in [x + 1 for x in range(max(self.df['Positives']))]:
            intervals.append(self._calculate_p(num_pos, alpha_value, df_col))
        return intervals
            
    def get_p_thresholds(self, alpha_value = 0.05, filepath = ''):
        columns = {}
        if not type(self.df) == pd.DataFrame:
            if os.path.exists(filepath + 'sim_results.csv'):
                self.df = pd.read_csv(filepath + 'sim_results.csv')
            else:
                self.simulate()
                self.analyse_sim()
                self.df.to_csv(filepath + 'sim_results.csv', index = False)
        for col in self.df.drop('Positives', axis = 1):
            print(col)
            columns[col] = self._column_p_thresholds(col, alpha_value)
        columns['Positives'] = self.df['Positives'].unique()
        return columns

    def prevelance_sim(self):
        pass


if __name__ == "__main__":
    sim = Simulator(PLATE_DIMENSIONS, POSITIVES_TO_GEN, CONTROL_POSITIONS, PLATES_TO_GEN)
    
    sim.simulate()
    #positives = sim.expected_positivities(0.453)
    sim.analyse_sim()
    #print((len(sim.df.loc[(sim.df['Positives'] == 27) & (sim.df['Max_Horizontal'] > 4)]) / len(sim.df.loc[sim.df['Positives'] == 27])) * 100)
    #print(positives)
    #sim.df['pos_rate'] = (sim.df['Positives'] / 93) * 100
    sim.df.to_csv('sim_results.csv', index = False)
    
    thresholds = pd.DataFrame(sim.get_p_thresholds())
    thresholds['p'] = '0.05'
    thresholds.to_csv('thresholds.csv')
    print(thresholds.head())
