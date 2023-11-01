#import cx_Oracle
import numpy as np
import pandas as pd
import src.functions as f
from datetime import datetime, timedelta


QUADRANTS = ('Q1', 'Q2', 'Q3', 'Q4')
QUAD_OFFSETS = {'Q1' : [0, 0], 'Q2' : [0, 1], 'Q3' : [1, 0], 'Q4' : [1, 1]}
LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
WELLS = {
    'Q1' : ('A01', 'C03', 'E05', 'G07', 'I09', 'K11', 'M13', 'O15'),
    'Q2' : ('A02', 'C04', 'E06', 'G08', 'I10', 'K12', 'M14', 'O16'),
    'Q3' : ('B01', 'D03', 'F05', 'H07', 'J09', 'L11', 'N13', 'P15'),
    'Q4' : ('B02', 'D04', 'F06', 'H08', 'J10', 'L12', 'N14', 'P16'),
    }
DINO_ART = """<br>
░░░░░░░░░░░████████░░░░░░░░░░<br>
░░░░░░░░░░███▄███████░░░░░░░░<br>
░░░░░░░░░░███████████░░░░░░░░<br>
░░░░░░░░░░███████████░░░<span style = "color:orange;">▓▓</span>░░░<br>
░░░░░░░░░░██████▄▀▄▀<span style = "color:red;">▓▓▓▓</span>░<span style = "color:orange;">▓▓</span>░<span style = "color:yellow;">▓</span><br>
░░░░░░░░░░█████████░░░<span style = "color:orange;">▓▓▓</span>░<span style = "color:yellow;">▓▓</span>░<br>
█░░░░░░░███████░░░░░░░░░░░░░░<br>
██░░░<span style = "color:purple;">▓▓</span>███████████░░░░░░░░░░░<br>
███░░░<span style = "color:purple;">▓▓▓</span>█████░░░█░░░░░░░░░░░<br>
████████<span style = "color:purple;">▓▓▓</span>████░░░░░░░░░░░░░░<br>
██████████<span style = "color:purple;">▓▓▓</span>██░░░░░░░░░░░░░░<br>
░███████████<span style = "color:purple;">▓▓▓</span>░░░░░░░░░░░░░░<br>
░░███████████░<span style = "color:purple;">▓▓</span>░░░░░░░░░░░░░<br>
░░░░████████░░░░░░░░░░░░░░░░░<br>
════░███░░██ ════════════════<br>
░░══░██░░░░█░░░░░░═░░░░░░░░░░<br>
═░░░░█░░░░░█░░░══░░░░═░░░░░░░<br>
░░░░░██░░░░██░░░░░░░░░░░══░░░<br>
_________________________________________<br>
Feature Unavailable in offline mode<br>        
"""


class Sample:
    """
    Stores data for an individual sample
    __init__(fam : int, vic : int, rox : int, barcode = '')
    
    Attributes
    ---------
    fam : int
        the FAM value
    vic : int
        the VIC value
    rox : int 
        the ROX value
    barcode : str
        the sample's barcode
    
    Methods
    -------
    all_data()
        returns data as a dictionary
    set_barcode(barcode)
        sets the sample barcode
    """
    def __init__(self, fam : int, vic : int, rox : int, barcode = ''):
        self.fam = fam
        self.vic = vic
        self.rox = rox
        if self.rox != 0:
            self.nfam = self.fam / self.rox
            self.nvic = self.vic / self.rox
        else:
            self.nfam = np.nan
            self.nvic = np.nan
        self.barcode = barcode
        
    def all_data(self) -> dict:
        """Returns the sample data as a dictionary"""
        return {'FAM': self.fam, 'VIC': self.vic, 'ROX': self.rox, 'nFAM': self.nfam, 'nVIC': self.nvic, 'barcode': self.barcode}
    
    def set_barcode(self, barcode : str):
        """Sets the sample barcode"""
        self.barcode = barcode
        

class Plate:
    """
    Stores the data of an entire plate. It can also create an HTML summary tab for the plate
    __init__(pool : str, array_code : str, glob : dict, thresholds : dict, date : str, cur)
    
    Attributes
    ----------
    pool : str
        The pool plate ID
    array_code : str
        The Tape ID for the plate
    globals : dict
        A dictionary containing various global variables obtained from a config for the analysis
    thresholds : dict
        A dictionary containing the analysis thresholds for this analysis
    date : str
        The read date of the plate in the format yyyy:mm:dd:HH:MM:SS
    cur
        A cx_Oracle Cursor object which is connected to the LIMS mirror
    sample_matrix
        A two-dimensional numpy array containing Sample objects which hold all the plate's data
    tab_str : str
        An HTML template for each analysis tab to be built from
    repooled : bool
        Whether the plate has been repooled or not
        
    Methods
    -------
    __getitem__(coordinates : str)
        Gets the item stored at the coordinates in the sample_matrix
    __setitem__(coordinates : str, new_value)
        Sets the item stored at the coordinates in the sample_matrix to the new_value
    set_barcodes(barcodes : list)
        Sets the barcode of every Sample on the plate to be the values in the given list
    barcodes_from_matrix(barcodes)
        Sets the barcode of every Sample on the plate to be the values in the given numpy array
    """
    def __init__(self, 
                 pool : str, 
                 array_code : str, 
                 glob : dict, 
                 thresholds : dict, 
                 date : str, 
                 cur, 
                 repooled = False,
                 df = None,
                 parent_plates = None,
                 info = None,
                 instruments = 'Unavailable',
                 comments = 'Unavailable',
                 escalations = []):
        self.cur = cur
        self.globals = glob
        self.date = date
        self.array_code = array_code
        self.sample_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        self.pool = pool
        self.thresholds = thresholds
        self.tab_str = self.globals['HTML_PLATE_TAB']
        self.df = df
        self.parent_plates = parent_plates
        self.info = info
        self.repooled = repooled
        self.platemaps = None
        self.instruments = instruments
        if not self.pool == None and not self.cur == None:
            self.find_instruments()
        self.comments = comments
        self.escalations = []

    def __getitem__(self, coordinates : str):
        """Gets the item stored at the coordinates in the sample_matrix"""
        true_coords = [LETTERS.index(coordinates[0]), int(coordinates[1:]) - 1]
        return self.sample_matrix[true_coords[0]][true_coords[1]]
    
    def __setitem__(self, coordinates : str, new_value):
        """Sets the item stored at the coordinates in the sample_matrix to the new_value"""
        true_coords = [LETTERS.index(coordinates[0]), int(coordinates[1:]) - 1]
        self.sample_matrix[true_coords[0]][true_coords[1]] = new_value
        
    def set_barcodes(self, barcodes : list):
        """
        Sets the barcode of every Sample on the plate to be the values in the given list
        
        Parameters
        ----------
        barcodes : list
            A list of tuples containing all of the barcodes for the plate in the format: (pool plate id, barcode, well)
        """
        for sample in barcodes:
            well = sample[2]
            if well[1] == '0':  # Removes the leading zeros is present
                well = well[0] + well[2]
            self[well].set_barcode(sample[1])
        self.data_as_df()
            
    def barcodes_from_matrix(self, barcodes):
        """
        Sets the barcode of every Sample on the plate to be the values in the given matrix
        
        Parameters
        ----------
        barcodes
            A numpy array with the same number of dimensions as the sample_matrix containing the barcodes
        """
        for row in range(16):
            for col in range(24):
                self.sample_matrix[row, col].set_barcode(barcodes[row, col])
        self.data_as_df()
            
    def data_as_df(self) -> dict:
        """Creates a data frame containing all the data stored in the plate in a format similar to the JoinLIMS.csv megajoin
        
        Sets self.df to be a dataframe with the following columns: 
            FAM, VIC, ROX, nFAM, nVIC, barcode, well
        """
        fam = []
        vic = []
        rox = []
        nfam = []
        nvic = []
        barcodes = []
        wells = []
        for row in range(16):
            for col in range(24):
                fam.append(self.sample_matrix[row, col].fam)
                vic.append(self.sample_matrix[row, col].vic)
                rox.append(self.sample_matrix[row, col].rox)
                nfam.append(self.sample_matrix[row, col].nfam)
                nvic.append(self.sample_matrix[row, col].nvic)
                barcodes.append(self.sample_matrix[row, col].barcode)
                wells.append(LETTERS[row] + str(col + 1))
        self.df = pd.DataFrame(dict(FAM = fam, VIC = vic, ROX = rox, nFAM = nfam, nVIC = nvic, barcode = barcodes, well = wells))
          
    def _lysis_elute(self) -> dict:
        """
        Queries LIMS to find all of the lysis and elution plates associated with each quadrant on the plate.
        Note: there is a bug in LIMS which means this does not work for lysis plates which were made manually (i.e. not on the hamilton).
        
        Returns
        -------
            A dictionary containing lists with the lysis and elution plates for each quadrant and the Pool Plate.
            Also there are some empty fields initialised in this dictionary as well for the Nexar, Araya, Hydrocycler and 384 Hamilton the 
            plate was run on.
        """
        result = {'Pool plate' : self.pool, 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
                  'Q1' : ['',''], 'Q2' : ['',''], 'Q3' : ['',''], 'Q4' : ['','']}
        wells = WELLS['Q1'] + WELLS['Q2'] + WELLS['Q3'] + WELLS['Q4']
        elutes = []
        query = self.globals['LY_EL_QUERY'].replace('$pool', self.pool).replace('$wells', str(wells))
        response = f.lims_query(query, self.cur)
        quadrants = ['Q1', 'Q2', 'Q3', 'Q4']
        for x in response:
            for quadrant in quadrants:
                if x[2] in WELLS[quadrant]:
                    elutes.append(x[1])
                    result[x[0]] = None
                    result[x[1]] = {}
                    result[quadrant] = x[0:2]
                    quadrants.remove(quadrant)
                    break
            if len(quadrants) == 0:
                break
        if self.globals['REPOOL_CHECK']:
            if f.repooled_check(elutes, self.cur, [self.globals['REPOOL_QUERY_1'], self.globals['REPOOL_QUERY_2']]):
                self.repooled = True
        return result
    
    def find_instruments(self):
        """
        Returns the pool plate as well as the nexar, araya, hydrocycler and 384 hamilton it was run on. It also returns the inactivation and
        elution plates relating to each quadrant.
        
        Parameters
        ----------
            plate: The array code.
            cur: A cx_Oracle cursor which connects to the LIMS mirror database.
        
        Returns
        -------
            dict containing the following keys:
                Pool plate: POOL ID
                Nexar
                Araya
                Hydrocycler
                Hamilton: 384_HAMILTON
                Q1, Q2, Q3, Q4: Lists containing [LYSIS ID, ELUTE ID] for the specific quadrant
            There are also keys matching each lysis plate with the DWP hamilton that lysis plate was run on as the value and
            Keys matching each elution plate with the Kingfisher and the Dragonfly that plate was run on
        """
        result = self._lysis_elute()
        plates = (self.pool, result['Q1'][0], result['Q1'][1], result['Q2'][0], result['Q2'][1], 
                  result['Q3'][0], result['Q3'][1], result['Q4'][0], result['Q4'][1])
        plates = tuple([x for x in plates if not x == None])
        instruments = f.lims_query(self.globals['INSTRUMENTS_QUERY'].replace('$plates', str(plates)), self.cur)
        for row in instruments:
            instrument = row[0]
            if row[1] == self.pool:
                if 'ARAYA' in instrument:
                    result['Araya'] = instrument
                elif 'NEXAR' in instrument:
                    result['Nexar'] = instrument
                elif 'HYDROCYCL' in instrument:
                    result['Hydrocycler'] = instrument
                elif 'HAM_384' in instrument:
                    result['Hamilton'] = instrument
            else:
                if 'HAM_DWP' in instrument:
                    result[row[1]] = instrument
                elif 'KF_' in instrument:
                    result[row[1]][0] = instrument
                elif 'DRAGONFLY' in instrument:
                    result[row[1]][1] = instrument
                
        result[''] = '  '  # This is needed to avoid KeyErrors later on when trying to find insturments for empty quadrants
        self.instruments = result
    
    def plate_info(self):
        """
        Sets plate info as a dictionary containing:
            Positive samples, number of patient PLODs and RNaseP failures across the whole plate and Q1, Q2, Q3, and Q4

        Returns:
            'Unavailable' (only if the plate is not in LIMS)
            
        WARNING
            The output of this is used later to build the buffer summary, if the format of the plate info is changed, the buffer
            Analysis.buffer_summary method might break
        """
        #print(self.df['barcode'].head())
        if self.cur == None:
            if not 'Sample' in self.df['barcode'].unique():
                self.info = 'Unavailable'
                return None
        sub_df = self.df.loc[(self.df['ROX'] >= self.thresholds['ROX_LIMIT']) & 
                             ~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES']))]
        totals = {'total' : len(self.df.loc[~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES']))])}

        total_pos = len(sub_df.loc[sub_df['nFAM'] >= self.thresholds['POSITIVE_THRESHOLD']])
        
        total_plod = len(sub_df.loc[(sub_df['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']) &
                                          (sub_df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD'])])
        
        high_plods = len(sub_df.loc[(sub_df['nFAM'] >= self.thresholds['POSITIVE_THRESHOLD'] - 1) &
                                    (sub_df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD'])])
        
        total_neg = len(sub_df.loc[(sub_df['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']) & 
                                   (sub_df['nVIC'] >= self.thresholds['nVIC_THRESHOLD'])])
        
        total_nvic_fails = len(sub_df.loc[(sub_df['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']) &
                                          (sub_df['nVIC'] < self.thresholds['nVIC_THRESHOLD'])])
        if totals['total'] > 0:
            positives = [str(total_pos) + ' (' + str(round((total_pos / totals['total']) * 100, 2)) + '%)', '']
            plods = [str(total_plod) + ' (' + str(round((total_plod / totals['total']) * 100, 2)) + '%, ' + str(high_plods) + ' high)', '']
        else:
            positives = [0, '']
            plods = [0, '']
        negs = [total_neg, '']
        nvic_fails = [total_nvic_fails, '']
        total_samples = [totals['total'], '']
        for quadrant in QUADRANTS:
            totals[quadrant] = len(self.df.loc[~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES'])) & 
                                   (self.df['Quadrant'] == quadrant)])
            
            quad_df = sub_df.loc[sub_df['Quadrant'] == quadrant]
            if totals[quadrant] > 0:
                quadrant_pos = len(quad_df.loc[quad_df['nFAM'] >= self.thresholds['POSITIVE_THRESHOLD']])
                positives.append(str(quadrant_pos) + ' (' + str(round((quadrant_pos / totals[quadrant]) * 100, 2)) + '%)')
            else:
                positives.append(0)
            plods.append(len(quad_df.loc[(quad_df['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']) &
                                         (quad_df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD'])]))
            negs.append(len(quad_df.loc[(quad_df['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']) &
                                        (quad_df['nVIC'] >= self.thresholds['nVIC_THRESHOLD'])]))
            nvic_fails.append(len(quad_df.loc[(quad_df['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']) &
                                              (quad_df['nVIC'] < self.thresholds['nVIC_THRESHOLD'])]))
            total_samples.append(totals[quadrant])
        blank_list = ['', '', '', '', '', '']
        if self.pool == None:
            instrument_info = blank_list
            nexar = blank_list
            araya = blank_list
            hydro = blank_list
            ham = blank_list
        else:
            instrument_info = ['', '', self.instruments['Q1'][0], self.instruments['Q2'][0], self.instruments['Q3'][0], self.instruments['Q4'][0]]
            nexar = [self.instruments['Nexar'], '', self.instruments[self.instruments['Q1'][0]], self.instruments[self.instruments['Q2'][0]], 
                     self.instruments[self.instruments['Q3'][0]], self.instruments[self.instruments['Q4'][0]]]
            araya = [self.instruments['Araya'], '', self.instruments['Q1'][1], self.instruments['Q2'][1], self.instruments['Q3'][1], self.instruments['Q4'][1]]
            hydro = [self.instruments['Hydrocycler'], '', self.instruments[self.instruments['Q1'][1]][0], self.instruments[self.instruments['Q2'][1]][0],
                     self.instruments[self.instruments['Q3'][1]][0], self.instruments[self.instruments['Q4'][1]][0]]
            ham = [self.instruments['Hamilton'], '', self.instruments[self.instruments['Q1'][1]][1], self.instruments[self.instruments['Q2'][1]][1],
                     self.instruments[self.instruments['Q3'][1]][1], self.instruments[self.instruments['Q4'][1]][1]]
        
        result = {
            self.array_code : (self.pool, '', 'Q1', 'Q2', 'Q3', 'Q4'),
                  'Positives' : positives,
                  'PLODs' : plods,
                  'Negatives' : negs,
                  'VIC Failures' : nvic_fails,
                  'Total Samples' : total_samples,
                  '' : blank_list,
                  'Instrument info' : instrument_info,
                  'Nexar' : nexar,
                  'Araya' : araya,
                  'Hydrocycler' : hydro,
                  '384 Hamilton' : ham
                  }
        self.info = result
        
    def rox_box(self):
        """Returns a dict with the Average ROX, ROX SD, ROX CV, num well with ROX < min rox threshold, num well with ROX > high rox threshold"""
        mean = self.df['ROX'].mean()
        sd = self.df['ROX'].std()
        low_rox_subset = self.df.loc[self.df['ROX'] < self.thresholds['ROX_LIMIT']]
        patient_low_rox = len(low_rox_subset.loc[~(low_rox_subset['barcode'].isin(self.globals['NON_PATIENT_CODES']))])
        return {'Average ROX' : [str(int(round(mean, 0))) + ' RFU'], 'Standard Deviation' : [int(round(sd, 0))], 
                'CV' : [str(round((sd / mean) * 100, 2)) + '%'],
                f'ROX < {self.thresholds["ROX_LIMIT"]}' : str(len(low_rox_subset)) + f' ({patient_low_rox} patient)',
                f'ROX >= {self.thresholds["HIGH_ROX"]}' : len(self.df.loc[self.df['ROX'] >= self.thresholds['HIGH_ROX']])}
    
    def _create_matrices(self):
        """
        Returns a dictionary containing 11 numpy matrices
        
        Returns
        -------
            dict containing the following matrices:
                nfam_matrix: Matrix containing the nFAM values as strings rounded to two decimals
                nvic_matrix: Contains the nVIC values as strings rounded to two decimals
                fam_matrix: Contains the FAM values
                vic_matrix: Contains the VIC values
                rox_matrix: Contains the ROX values
                result_matrix: A matrix representing the platemap of results based on the nFAM value. 0 = Negative, 1 = PLOD, 2 = Positive
                vic_result_matrix: The RNaseP result. 0 = Negative, 1 = Positive
                flag_matrix: A matrix of warnings for wells. Warnings include: PLOD, HI PLOD, VIC FAIL, Pos fail, Neg fail, etc...
                flag_numbers: A matrix of numbers which tells plotly what colour each warning in the notifications tab should be displayed as
                barcode_matrix: A platemap of the barcode preffixes of each sample on the plate
                barcode_colours: A matrix where each unique barcode preffix is assigned a number (used to determine the colours of barcodes)
        """
        nfam_matrix = np.array([[None for _ in range(24)] for _ in range(16)])  # Initialise all the matrices
        vic_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        fam_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        rox_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        result_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        vic_result_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        nvic_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        flag_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        flag_numbers = np.array([[None for _ in range(24)] for _ in range(16)])
        barcode_colours = np.array([[None for _ in range(24)] for _ in range(16)])
        barcode_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        flags = []
        quadrants = []
        barcodes = {}
        quadrant = [(('Q1', 'Q2'), ('Q3', 'Q4')), -1, 0]
        barcode_count = 0
        for row in range(16):
            quadrant[1] += 1
            for col in range(24):
                quadrants.append(quadrant[0][quadrant[1] % 2][quadrant[2] % 2])
                quadrant[2] += 1
                sample = self.sample_matrix[row, col].all_data()
                if not sample['barcode'] in barcodes.keys():
                    barcodes[sample['barcode']] = barcode_count
                    barcode_count += 1
                barcode_colours[row, col] = barcodes[sample['barcode']]
                barcode_matrix[row, col] = sample['barcode']
                fam_matrix[row, col] = sample['FAM']
                vic_matrix[row, col] = sample['VIC']
                rox_matrix[row, col] = sample['ROX']
                if self.thresholds['POSITIVE_THRESHOLD'] - 0.01 <= sample['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']:
                    nfam_matrix[row, col] = str(self.thresholds['POSITIVE_THRESHOLD'] - 0.01)
                elif self.thresholds['NEGATIVE_THRESHOLD'] - 0.01 <= sample['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']:
                    nfam_matrix[row, col] = str(self.thresholds['NEGATIVE_THRESHOLD'] - 0.01)
                else:
                    nfam_matrix[row, col] = str(round(sample['nFAM'], 2))
                if self.thresholds['nVIC_THRESHOLD'] - 0.01 <= sample['nVIC'] < self.thresholds['nVIC_THRESHOLD']:
                    nvic_matrix[row, col] = str(self.thresholds['nVIC_THRESHOLD'] - 0.01)
                else:    
                    nvic_matrix[row, col] = str(round(sample['nVIC'], 2))
                sample_well = LETTERS[row] + str(col + 1)
                if sample['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']:
                    result_matrix[row, col] = 0
                elif self.thresholds['NEGATIVE_THRESHOLD'] <= sample['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']:
                    result_matrix[row, col] = 1
                else:
                    result_matrix[row, col] = 2
                if sample['nVIC'] < self.thresholds['nVIC_THRESHOLD']:
                    vic_result_matrix[row, col] = 0
                else:
                    vic_result_matrix[row, col] = 1
                warning = 'None'
                warn_number = 0
                if sample['ROX'] < self.thresholds['ROX_LIMIT']:
                    if sample['barcode'] == 'Con':
                        if sample_well in self.globals['ACCUPLEX_WELLS']:
                            warning = 'ROX accu'
                            warn_number = 1
                        elif sample_well in self.globals['QNOS_WELLS']:
                            warning = 'ROX qnos'
                            warn_number = 1
                        elif sample_well in self.globals['NEGCON_WELLS']:
                            warning = 'ROX negcon'
                            warn_number = 1
                    elif sample['barcode'] in self.globals['NON_PATIENT_CODES']:
                        if sample['barcode'] == 'SPA':
                            warning = 'SPA ROX'
                        else:
                            warning = 'ENV ROX'
                        warn_number = 6
                    else:
                        warning = 'ROX fail'
                        warn_number = 6
                elif sample['barcode'] == 'Con':  # I.e if control
                    if sample_well in self.globals['ACCUPLEX_WELLS'] + self.globals['QNOS_WELLS']:  # I.e if poscon
                        if sample_well in self.globals['ACCUPLEX_WELLS']:
                            if sample['nVIC'] >= self.thresholds['nVIC_THRESHOLD']:
                                warning = 'VIC accu'  # This warning is used elsewhere in code, if it is changed, also change that line
                                warn_number = 1
                        if sample['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']:
                            warning = 'Pos fail'  # This warning is used elsewhere in code, if it is changed, also change that line
                            warn_number = 1
                    elif sample_well in self.globals['NEGCON_WELLS'] and sample['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']:
                        warning = 'Neg fail'  # This warning is used elsewhere in code, if it is changed, also change that line
                        warn_number = 1
                elif sample['barcode'] in self.globals['NON_PATIENT_CODES']:  # If has no associated barcode
                    if not sample['barcode'] == 'SPA':
                        if sample['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']:
                            warning = 'Contam'  # Can we be sure that barcodeless wells should always be negative?
                            warn_number = 5
                else:  # I.e if patient sample
                    if sample['nFAM'] < self.thresholds['NEGATIVE_THRESHOLD']:
                        if sample['nVIC'] >= self.thresholds['nVIC_THRESHOLD']:
                            if (sample['ROX'] >= self.thresholds['HIGH_ROX'] - self.globals['MM_ONLY_RULES']['MIN_ROX'] and 
                                self.thresholds['nVIC_THRESHOLD'] <= sample['nVIC'] < self.thresholds['nVIC_THRESHOLD'] + 
                                self.globals['MM_ONLY_RULES']['MAX_nVIC'] and self.globals['MM_ONLY_RULES']['FAM_TO_VIC_LIMS'][0]
                                < sample['FAM'] / sample['VIC'] < self.globals['MM_ONLY_RULES']['FAM_TO_VIC_LIMS'][1]):  # Detects MM-only signals
                                warning = 'MM-only'  # This might falsely flag some wells, but warnings should always be reviewed by someone anyway
                                warn_number = 2
                        else:  # I.e if nFAM and nVIC is negative
                            warning = 'VIC fail'
                            warn_number = 4
                    elif sample['nFAM'] < self.thresholds['POSITIVE_THRESHOLD'] - 1:
                        warning = 'PLOD'
                        warn_number = 8
                    elif sample['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']:
                        warning = 'HI PLOD'
                        warn_number = 7
                flag_matrix[row, col] = warning
                flags.append(warning)
                flag_numbers[row, col] = warn_number
        self.df['Flags'] = flags
        self.df['Quadrant'] = quadrants
        self.detect_escalations_384(flag_matrix)
        return dict(nfam_matrix = nfam_matrix, rox_matrix = rox_matrix, nvic_matrix = nvic_matrix, result_matrix = result_matrix, 
            vic_result_matrix = vic_result_matrix, fam_matrix = fam_matrix, vic_matrix = vic_matrix, flag_matrix = flag_matrix, 
            flag_numbers = flag_numbers, barcode_colours = barcode_colours, barcode_matrix = barcode_matrix)
    
    def detect_escalations_384(self, flag_matrix):
        """
        Detects if the plate needs to be escalated because it has too many RNaseP failures, ROX failures or PLODs and appends the escalation
        self.escalations
        """
        if (flag_matrix == 'VIC fail').sum() >= self.globals['SOP_nVIC_ESCALATION_LIMIT'][0]:
            self.escalations.append(f'Level {self.globals["SOP_nVIC_ESCALATION_LIMIT"][1]} - {self.globals["SOP_nVIC_ESCALATION_LIMIT"][0]} or more RNaseP failures')
        if (flag_matrix == 'ROX fail').sum() >= self.globals['SOP_ROX_FAIL_LIMIT'][0]:
            self.escalations.append(f'Level {self.globals["SOP_ROX_FAIL_LIMIT"][1]} - {self.globals["SOP_ROX_FAIL_LIMIT"][0]} or more ROX fails')
        if (flag_matrix == 'PLOD').sum() >= self.globals['SOP_PLOD_LIMIT'][0]:
            self.escalations.append(f'Level {self.globals["SOP_PLOD_LIMIT"][1]} - {self.globals["SOP_PLOD_LIMIT"][0]} or more PLODs')
    
    def detect_escalations_quadrant(self, matrices, quadrant):
        """Detects if the plate needs to be escalated because a failure has invalidated samples"""
        if np.isin(matrices['flag_matrix'], ('VIC accu', 'Pos fail', 'ROX qnos')).sum() >= 2:
            if 'VIC accu' in matrices['flag_matrix']:
                self.escalations.append(f'Level 2 - The qnostic has failed on {quadrant}, and the accuplex in the same quadrant contains RNaseP')
            else:
                self.escalations.append(f'Level 2 - Both positive controls on {quadrant} have failed')
        if 'Neg fail' in matrices['flag_matrix'] or 'ROX negcon' in matrices['flag_matrix']:
            brk = False
            for row in range(8):
                for col in range(12):
                    if not matrices['barcode_matrix'][row, col] in self.globals['NON_PATIENT_CODES']:
                        if float(matrices['nfam_matrix'][row, col]) >= self.thresholds['POSITIVE_THRESHOLD']:
                            self.escalations.append(f'Level 2 - Negcon fail on {quadrant} has invalidated samples')
                            brk = True
                            break
                if brk:
                    break
                    
    def _quadrant_matrices(self, matrices : dict) -> dict:
        """
        Extracts the four quadrants from a dictionary of 384-well numpy matrices and returns the dictionary with these new matrices
        added into it. This method also checks for striping of positive samples on quadrants based on service guidance and alters the
        flag_matrix accordingly
        
        Parameters
        ----------
            matrices: A dictionary containing various 384-well matrices, including a flag matrix
            
        Returns
        -------
            dict containing all the matrices passed to the function with new keys: Q1, Q2, Q3 & Q4 who's values are dictionaries containing
            all the matrices for that individual quadrant
        """
        new_matrices = {'384' : matrices, 'Q1' : {'pos' : 0, 'total' : 0}, 'Q2' : {'pos' : 0, 'total' : 0}, 
                        'Q3' : {'pos' : 0, 'total' : 0}, 'Q4' : {'pos' : 0, 'total' : 0}}
        for matrix in matrices:
            for quadrant in QUADRANTS:
                new_matrices[quadrant][matrix] = np.array([[None for _ in range(12)] for _ in range(8)])
        for row in range(8):
            for col in range(12):
                for matrix in matrices:
                    for quadrant in QUADRANTS:
                        new_matrices[quadrant][matrix][row, col] = matrices[matrix][row * 2 + QUAD_OFFSETS[quadrant][0], col * 2 + QUAD_OFFSETS[quadrant][1]]
                        
        # Find out how many positives there are in each quadrant:
        for quadrant in QUADRANTS:
            for row in range(8):
                for col in range(12):
                    if not new_matrices[quadrant]['barcode_matrix'][row, col] in self.globals['NON_PATIENT_CODES']:
                        new_matrices[quadrant]['total'] += 1
                        if float(new_matrices[quadrant]['nfam_matrix'][row, col]) >= self.thresholds['POSITIVE_THRESHOLD']:
                            new_matrices[quadrant]['pos'] += 1

            if new_matrices[quadrant]['pos'] >= min(self.globals['STRIPE_LIMIT']):
                if (new_matrices[quadrant]['pos'] / new_matrices[quadrant]['total'] * 100) <= self.globals['STIPE_CHECK_LIMIT']:
                    new_matrices[quadrant]['flag_matrix'], new_matrices[quadrant]['flag_numbers'] = f.find_stripes(new_matrices[quadrant]['nfam_matrix'], 
                                                                                                                  new_matrices[quadrant]['flag_matrix'], 
                                                                                                                  new_matrices[quadrant]['flag_numbers'],
                                                                                                                  self.globals,
                                                                                                                  self.thresholds['POSITIVE_THRESHOLD'])
                    if np.any(new_matrices[quadrant]['flag_matrix'] == 'Stripe'):
                        stripes = np.where(new_matrices[quadrant]['flag_matrix'] == 'Stripe')
                        for idx in range(len(stripes[0])):
                            new_matrices['384']['flag_matrix'][stripes[0][idx] * 2 + QUAD_OFFSETS[quadrant][0], 
                                                               stripes[1][idx] * 2 + QUAD_OFFSETS[quadrant][1]] = 'Stripe'
                            new_matrices['384']['flag_numbers'][stripes[0][idx] * 2 + QUAD_OFFSETS[quadrant][0], 
                                                               stripes[1][idx] * 2 + QUAD_OFFSETS[quadrant][1]] = 3
                            
            self.detect_escalations_quadrant(new_matrices[quadrant], quadrant)
        return new_matrices
    
    def create_platemaps(self):
        """
        Uses plotly's heatmap function to create platemaps for the 384-well and quadrant levels
        These platemaps are stored in self.platemaps in a dictionary. The platemaps themselves are strings representing the HTML/js code for
        the plots
        """
        matrices = self._create_matrices()
        all_matrices = self._quadrant_matrices(matrices)
        _384 = f.plot_platemap(all_matrices['384'], 1600, 1000, '384 platemap', self.globals)
        q1 = f.plot_platemap(all_matrices['Q1'], 800, 500, 'Quadrant 1', self.globals, quadrant = 'Q1')
        q2 = f.plot_platemap(all_matrices['Q2'], 800, 500, 'Quadrant 2', self.globals, quadrant = 'Q2')
        q3 = f.plot_platemap(all_matrices['Q3'], 800, 500, 'Quadrant 3', self.globals, quadrant = 'Q3')
        q4 = f.plot_platemap(all_matrices['Q4'], 800, 500, 'Quadrant 4', self.globals, quadrant = 'Q4')
        
        self.matrices = all_matrices
        self.platemaps = {'384' : _384, 'Q1' : q1, 'Q2' : q2, 'Q3' : q3, 'Q4' : q4}
    
    def scatter_charts(self) -> dict:
        """
        Creates scatter charts of ROX vs FAM, ROX vs nFAM, ROX vs VIC, ROX vs nVIC and nFAM vs nVIC and returns these plotly plots in a dict
        
        Returns
        -------
            A dict containing the plotly graphs:
                rvf: ROX vs FAM
                rvnf: ROX vs nFAM
                rvv: ROX vs VIC
                rvnv: ROX vs nVIC
                nfvnv: nFAM vs nVIC
        """
        rvf = f.scatter_plot(self.df, 'ROX', 'FAM', self.globals['BACKGROUND_COLOUR'], title = 'ROX vs FAM')
        rvnf = f.scatter_plot(self.df, 'ROX', 'nFAM', self.globals['BACKGROUND_COLOUR'], title = 'ROX vs nFAM')
        rvv = f.scatter_plot(self.df, 'ROX', 'VIC', self.globals['BACKGROUND_COLOUR'], title = 'ROX vs VIC')
        rvnv = f.scatter_plot(self.df, 'ROX', 'nVIC', self.globals['BACKGROUND_COLOUR'], title = 'ROX vs nVIC')
        nfvnv = f.scatter_plot(self.df, 'nVIC', 'nFAM', self.globals['BACKGROUND_COLOUR'], title = 'nFAM vs nVIC')
        
        rvf = f.add_plot_lines(rvf, [['x', self.thresholds['ROX_LIMIT'], 'Orange'],
                                     ['x', self.thresholds['HIGH_ROX'], 'Orange'],], self.globals['GRAPH_LINE_SIZE'])
        rvnf = f.add_plot_lines(rvnf, [['y', self.thresholds['NEGATIVE_THRESHOLD'], 'Green'],
                                     ['y', self.thresholds['POSITIVE_THRESHOLD'], 'Red'],
                                     ['x', self.thresholds['ROX_LIMIT'], 'Orange'],
                                     ['x', self.thresholds['HIGH_ROX'], 'Orange'],], self.globals['GRAPH_LINE_SIZE'])
        rvv = f.add_plot_lines(rvv, [['x', self.thresholds['ROX_LIMIT'], 'Orange'],
                                     ['x', self.thresholds['HIGH_ROX'], 'Orange'],], self.globals['GRAPH_LINE_SIZE'])
        rvnv = f.add_plot_lines(rvnv, [['y', self.thresholds['nVIC_THRESHOLD'], 'Yellow'],
                                     ['x', self.thresholds['ROX_LIMIT'], 'Orange'],
                                     ['x', self.thresholds['HIGH_ROX'], 'Orange'],], self.globals['GRAPH_LINE_SIZE'])
        nfvnv = f.add_plot_lines(nfvnv, [['y', self.thresholds['NEGATIVE_THRESHOLD'], 'Green'],
                                     ['y', self.thresholds['POSITIVE_THRESHOLD'], 'Red'],
                                     ['x', self.thresholds['nVIC_THRESHOLD'], 'Yellow']], self.globals['GRAPH_LINE_SIZE'])
        return dict(rvf = rvf, rvnf = rvnf, rvv = rvv, rvnv = rvnv, nfvnv = nfvnv)
    
    def check_plate_flip(self):
        """Checks if the plate could contain a flipped elution plate. Warning: This function will not automatically update in the event
        that the control locations are changed in the config"""
        for quadrant in QUADRANTS:
            possible_accu = self.sample_matrix[0 + QUAD_OFFSETS[quadrant][0], 2 * 2 + QUAD_OFFSETS[quadrant][1]]
            possible_qnos = self.sample_matrix[0 + QUAD_OFFSETS[quadrant][0], 0 + QUAD_OFFSETS[quadrant][1]]
            if min(possible_accu.nfam, possible_qnos.nfam) >= self.thresholds['NEGATIVE_THRESHOLD']:
                if self.sample_matrix[0 + QUAD_OFFSETS[quadrant][0], 1 * 2 + QUAD_OFFSETS[quadrant][1]].nfam < self.thresholds['POSITIVE_THRESHOLD']:
                    if possible_accu.nvic < self.thresholds['nVIC_THRESHOLD']:
                        actual_accu_well = self.sample_matrix[7 * 2 + QUAD_OFFSETS[quadrant][0], 9 * 2 + QUAD_OFFSETS[quadrant][1]]
                        if actual_accu_well.nvic >= self.thresholds['nVIC_THRESHOLD']:
                            return True
        return False
            
    
    def get_comments(self) -> dict:
        """
        Returns a dictionary containing the comments on each plate which went into the pool plate, and the comments appended to the pool plate 
        itself (This is done becuase the official LIMS comment trail feature is broken, lol).
        
        Parameters:
            plates: A dictionary containing all the various plate names in the following format:
                {
                'Q1': [<elution plate>, <inact plate>],
                'Q2': [<elution plate>, <inact plate>],
                'Q3': [<elution plate>, <inact plate>],
                'Q4': [<elution plate>, <inact plate>],
                'Pool':<pool plate>
                }
            cur: A cx_Oracle cursor which connects to the LIMS mirror database.
            
            Returns:
                dict
        """
        plates = {
            'Q1' : [self.instruments['Q1'][1], self.instruments['Q1'][0]],
            'Q2' : [self.instruments['Q2'][1], self.instruments['Q2'][0]],
            'Q3' : [self.instruments['Q3'][1], self.instruments['Q3'][0]],
            'Q4' : [self.instruments['Q4'][1], self.instruments['Q4'][0]],
            'Pool' : self.instruments['Pool plate']
            }
        all_comments = {'Q1' : [], 'Q2' : [], 'Q3' : [], 'Q4' : []}
        comments = {'Q1' : {}, 'Q2' : {}, 'Q3' : {}, 'Q4' : {}, 'Pool' : []}
        all_plates = list(plates['Q1'] + plates['Q2'] + plates['Q3'] + plates['Q4'])
        all_plates.append(plates['Pool'])
        query = self.globals['COMMENTS_QUERY'].replace('$all_plates', str(tuple(all_plates)))
        try:
            comments_df = pd.DataFrame(f.lims_query(query, self.cur), columns = ('comment', 'plate'))
        except ValueError:#cx_Oracle.DatabaseError:
            self.comments = "ERROR - Could not fetch comments"
            return None
        for quadrant in QUADRANTS:
            comms = comments_df.loc[comments_df['plate'] == plates[quadrant][1]]['comment']
            plate_comms = []
            for com in comms:
                plate_comms.append(com)
                all_comments[quadrant].append(com)
            comments[quadrant][plates[quadrant][1]] = plate_comms
            plate_comms = []
            comms = comments_df.loc[comments_df['plate'] == plates[quadrant][0]]['comment']
            for com in comms:
                if not com in all_comments[quadrant]:
                    plate_comms.append(com)
                    all_comments[quadrant].append(com)
            comments[quadrant][plates[quadrant][0]] = plate_comms
        comms = comments_df.loc[comments_df['plate'] == plates['Pool']]['comment']
        all_comments = all_comments['Q1'] + all_comments['Q2'] + all_comments['Q3'] + all_comments['Q4']
        for com in comms:
            if not com in all_comments:
                comments['Pool'].append(com)
        self.comments = f.format_comments(comments)
    
    def check_if_prio(self):
        """Returns True or False based on whether the plate is priority or not"""
        if 'priority' in self.comments.lower() or not len(set(self.globals['PRIO_CODES'] + self.df['barcode'].unique().tolist())
                                                      ) == len(self.globals['PRIO_CODES'] + self.df['barcode'].unique().tolist()):
            return True
        return False
    #test
    def check_if_vip(self):
        """Returns True or False based on whether the plate is priority or not"""
        if ' vip ' in self.comments.lower() or '(vip)' in self.comments.lower():
            return True
        return False
    
    def create_tab(self, plate_str : str):
        """
        Builds the HTML code for this plate's analysis tab
        
        returns
        -------
            str of the HTML code for the plate analysis tab
        """
        if self.repooled:
            plate_str += ' (<span style = "color:#e60000">repooled</span>)'
        platemaps = self.platemaps
        if self.pool == None and not 'Sample' in self.df['barcode'].unique():
            info = 'Unavailable'
        else:
            info = pd.DataFrame(self.info).to_html(index = False)
        scatter_charts = self.scatter_charts()
        
        if self.check_plate_flip():
            plate_str += ' (<span style = "color:#e60000">possible plate flip!</span>)'

        self.tab_str = self.tab_str.replace('£tab_title£', plate_str)
        self.tab_str = self.tab_str.replace('£plate£', str(self.array_code))
        self.tab_str = self.tab_str.replace('£background_color£', self.globals['BACKGROUND_COLOUR'])
        self.tab_str = self.tab_str.replace('£384heatmap£', platemaps['384'].render())
        self.tab_str = self.tab_str.replace('£Q1£', platemaps['Q1'].render())
        self.tab_str = self.tab_str.replace('£Q2£', platemaps['Q2'].render())
        self.tab_str = self.tab_str.replace('£Q3£', platemaps['Q3'].render())
        self.tab_str = self.tab_str.replace('£Q4£', platemaps['Q4'].render())
        self.tab_str = self.tab_str.replace('£plate_info£', info)
        self.tab_str = self.tab_str.replace('£roxbox£', pd.DataFrame(self.rox_box()).to_html(index = False))
        self.tab_str = self.tab_str.replace('£escalations£', f.format_escalations(self.escalations))
        self.tab_str = self.tab_str.replace('£rvf£', scatter_charts['rvf'].render())
        self.tab_str = self.tab_str.replace('£rvnf£', scatter_charts['rvnf'].render())
        self.tab_str = self.tab_str.replace('£rvv£', scatter_charts['rvv'].render())
        self.tab_str = self.tab_str.replace('£rvnv£', scatter_charts['rvnv'].render())
        self.tab_str = self.tab_str.replace('£nfvnv£', scatter_charts['nfvnv'].render())
        self.tab_str = self.tab_str.replace('£comments£', self.comments)
        return self.tab_str

class Analysis:
    """
    Runs the analysis and creates the output HTML file for Pool Helper. This Class obtains and stores all the data from either araya files or
    directly from the LIMS mirror for plates in a run using the classes Plate and Sample, then uses the methods of these classes to build the
    HTML output. It's a little bit messy compared to the other classes, but it gets the job done.
    
    Attributes
    ----------
        cur : A cx_Oracle cursor object (or 'None' if in offline mode)
            A connection to the LIMS mirror database
        admin : bool
            Whether or not the user is an admin
        mirrorless : bool
            Whether or not a connection to the LIMS mirror is available (self.cur should be set to None if this is True)
        globals : dict
            Contains the program's config variables which have been obtained from the shared config file
        html : str
            A string of html template into which the analysis outputs can be inserted into
        thresholds : dict
            Contains the values for each araya's thresholds
        plates : dict
            The keys will be each plate in the analysis batch's array code. The values will be Plate objects which store all the plate's data
        date : datetime date object
            The data the plates were run on (this will match the date of the first plate in the analysis batch, if plates from multiple batches
            are analysed, the date will only reflect the date of the first plate in the plates)
        restamped : list
            List of all the plates which have been restamped in the three days prior, and including the date of the first plate in the batch
        summary : pandas.DataFrame object
            A table containing the buffer summary data for this run of plates
        
    Methods
    -------
        set_thresholds()
            Adds new values to the self.thresholds dictionary which relate to the thresholds of the araya this batch of plates was run on
            (or more specifically, the araya which the first plate in the batch was run on. If plates from multiple batches at once are
             analysed, it is possible somple plates will recieve the wrong araya thresholds. Therefore it is important when analysing plates
             with Pool Helper to make sure you only analyse plates from the same araya run)
        _summary_buffer(df, plate, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic)
            A subfunction which appends data to the buffer summary, this method should be used for plates which are buffer plates
        _summary_patient(df, plate, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic, last_plate_buffer)
            A subfunction which appends data to the buffer summary, this method should be used for plates which are patient plates
        buffer_summary()
            Creates a buffer summary. This summary is in the form of a pd.DataFrame, which is returned by the method
        run_analysis()
            Builds the html output file based on the data in each of the plates in the run
    """
    def __init__(self, version, first_array, glob, thresholds, cur, admin = False, from_files = False, mirrorless = False, filepath = './/Araya Files//'):
        self.cur = cur
        self.admin = admin
        self.mirrorless = mirrorless
        self.globals = glob
        self.html = self.globals['HTML_FIRST_TAB']
        self.html = self.html.replace('£version£', version)
        self.thresholds = thresholds
        queries = (self.globals['GET_FILES_QUERY_1'], self.globals['GET_FILES_QUERY_2'], self.globals['POOL_QUERY'])
        self.plates = f.pipe(first_array, self.globals, self.thresholds, self.cur, queries, filepath = filepath, from_files = from_files)
        self.date = datetime.strptime(self.plates[list(self.plates.keys())[0]].date[0:10], '%Y:%m:%d')
        self.restamped = []
        if self.globals['RESTAMP_CHECK']:
            print('Finding restamps...')
            self.restamped = f.restamp_finder(self.date - timedelta(days = 3), self.date + timedelta(days = 1), self.cur, self.globals['RESTAMP_QUERY'])
        self.set_thresholds()
        pools = tuple([x.pool for x in list(self.plates.values()) if x.pool != None])
        pools_str = str(pools)
        if len(pools) == 1:
            pools_str = pools_str.replace(',', '')
        query = self.globals['BARCODES_QUERY'].replace('$pools', pools_str)
        
        barcode_dict = {}
        con_wells_letter = self.globals['ACCUPLEX_WELLS'] + self.globals['QNOS_WELLS'] + self.globals['NEGCON_WELLS']
        if self.cur == None:
            barcode_matrix = np.array([['Sample' for _ in range(24)] for _ in range(16)]) #f.extract_barcodes(str(plate), CONNECTION).to_numpy()  # barcode preffixes
            con_wells = tuple([(LETTERS.index(x[0]), int(x[1:]) - 1) for x in con_wells_letter])
            for x in con_wells:
                barcode_matrix[x] = 'Con'
            barcode_matrix = np.loadtxt(open("barcodes.csv", "r"), delimiter=",", dtype=str)
            for plate in self.plates:
                self.plates[plate].barcodes_from_matrix(barcode_matrix)
                self.plates[plate].data_as_df()
                self.plates[plate].create_platemaps()
                self.plates[plate].plate_info()
            self.summary = 'Unavailable'
        else:
            try:
                barcodes = f.lims_query(query, cur)
                for pool in pools:
                    barcode_dict[pool] = []
                for sample in barcodes:
                    if sample[2] in con_wells_letter:
                        if len(sample[1]) > 0:
                            sample = (sample[0], 'Con', sample[2])
                    barcode_dict[sample[0]].append(sample)
            except ValueError:#cx_Oracle.DatabaseError:
                pass
            for plate in self.plates:
                if self.plates[plate].pool != None:
                    self.plates[plate].set_barcodes(barcode_dict[self.plates[plate].pool])
                    self.plates[plate].get_comments()
                self.plates[plate].data_as_df()
                self.plates[plate].create_platemaps()
                self.plates[plate].plate_info()
                
            self.summary = self.buffer_summary()
        
    def set_thresholds(self):
        """
        Adds five new entries to self.thresholds which hold the values of the thresholds for the current araya being used
        
        NOTE
            This function iterates through the plates, querying LIMS to find the araya. It will stop at the first plate which 
            has an araya associated with it in LIMS and will use this araya for the whole batch. Therefore some plates could be 
            analysed using the wrong thresholds if plates from multiple araya runs are analysed at once. If no plate has an araya
            in LIMS, the function will default to using araya 1's thresholds
        """
        if self.cur == None or self.admin:
            while True:
                araya = input("Which araya? (1 / 2 / 3): ")
                try:
                    int(araya)
                    break
                except ValueError:
                    print("ERROR: Input must be a number")
        else:
            for plate in self.plates:
                araya = f.get_araya(self.globals['ARAYA_QUERY'].replace('$plate', plate), self.cur)
                if not araya == None:
                    break
        if not araya == None:
            self.thresholds['NEGATIVE_THRESHOLD'] = self.thresholds[f'NEGATIVE_THRESHOLD_A{araya[-1]}']
            self.thresholds['POSITIVE_THRESHOLD'] = self.thresholds[f'POSITIVE_THRESHOLD_A{araya[-1]}']
            self.thresholds['nVIC_THRESHOLD'] = self.thresholds[f'nVIC_THRESHOLD_A{araya[-1]}']
            self.thresholds['ROX_LIMIT'] = self.thresholds[f'ROX_LIMIT_A{araya[-1]}']
            self.thresholds['HIGH_ROX'] = self.thresholds[f'HIGH_ROX_A{araya[-1]}']
            print('\n' + araya)
        else:
            self.thresholds['NEGATIVE_THRESHOLD'] = self.thresholds['NEGATIVE_THRESHOLD_A1']
            self.thresholds['POSITIVE_THRESHOLD'] = self.thresholds['POSITIVE_THRESHOLD_A1']
            self.thresholds['nVIC_THRESHOLD'] = self.thresholds['nVIC_THRESHOLD_A1']
            self.thresholds['ROX_LIMIT'] = self.thresholds['ROX_LIMIT_A1']
            self.thresholds['HIGH_ROX'] = self.thresholds['HIGH_ROX_A1']
            print('\nNo associated araya, using thresholds for araya 1')
            araya = 'Araya 1'
        print(f"""Using thresholds:
          Negative = {self.thresholds['NEGATIVE_THRESHOLD']}
          Positive = {self.thresholds['POSITIVE_THRESHOLD']}
          nVIC = {self.thresholds['nVIC_THRESHOLD']}
          Low ROX limit = {self.thresholds['ROX_LIMIT']}
          high ROX limit = {self.thresholds['HIGH_ROX']}""")
        self.html = self.html.replace('£araya£', araya)
          
    def _summary_buffer(self, df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic):
        """
        Appends the relevant data to the buffer summary (df). This function is for buffer plates
        
        Parameters
        ----------
            df : dict
                The buffer summary as it is now. This function will append data to the lists within this dictionary
            plate_pos : pd.Series object
                Contains strings of the plate coordinates of all the positive wells on the plate
            plate_plods : pd.Series object
                Contains strings of the plate coordinates of all the PLOD wells on the plate
            plate_vic : pd.Series object
                Contains strings of the plate coordinates of all the nVIC positive wells on the plate
            previous_fam : pd.Series object
                Strings of all of the wells in the previous plate which were positive
            previous_vic : pd.Series object
                Strings of all the wells in the previous plate which were nVIC positive
                
        Returns
        -------
            The updated buffer summary dictionary, df
        """
        df['plate_type'].append('Possible Buffer')
        df['test_channel'].append('-')
        df['patient_samples'].append(0)
        df['positives'].append(len(plate_pos))
        df['positive_wells'].append(str(list(plate_pos)).replace('[', '').replace(']', '').replace("'", ''))
        df['vic_pos_wells'].append(str(list(plate_vic)).replace('[', '').replace(']', '').replace("'", ''))
        df['vic_fails'].append('-')
        df['accu_fails'].append('-')
        df['negcon_fails'].append('-')
        df['poscon_fails'].append('-')
        df['pos_rate'].append('-')
        carry_overs = f.detect_carryover(plate_pos, plate_vic, plate_plods, previous_fam, previous_vic)
        df['pos_punch'].append(carry_overs[0])
        df['vic_punch'].append(carry_overs[1])
        df['plod_punch'].append(carry_overs[2])
        
        return df
    
    def _summary_patient(self, df, plate, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic, last_plate_buffer):
        """
        Appends the relevant data to the buffer summary (df). This function is for patient plates
        
        Parameters
        ----------
            df : dict
                The buffer summary as it is now. This function will append data to the lists within this dictionary
            plate : Plate object
                The current plate being analysed
            plate_pos : pd.Series object
                Contains strings of the plate coordinates of all the positive wells on the plate
            plate_plods : pd.Series object
                Contains strings of the plate coordinates of all the PLOD wells on the plate
            plate_vic : pd.Series object
                Contains strings of the plate coordinates of all the nVIC positive wells on the plate
            previous_fam : pd.Series object
                Strings of all of the wells in the previous plate which were positive
            previous_vic : pd.Series object
                Strings of all the wells in the previous plate which were nVIC positive
            last_plate_buffer : bool
                Whether or not the previous plate in the run was a buffer plate
                
        Returns
        -------
            The updated buffer summary dictionary, df
        """
        df['plate_type'].append('Patient')
        channels = ''
        comments = plate.comments
        if 'VIP' in comments.upper():
            channels += 'VIP, '
        if 'OLT' in comments.upper():
            channels += 'OLT, '
        if 'RTS' in comments.upper():
            channels += 'RTS, '
        if 'HTK' in comments.upper():
            channels += 'HTK, '
        if 'PRK' in comments.upper():
            channels += 'PRK, '
        if 'AVA' in comments.upper():
            channels += 'AVA, '
        if 'priority' in comments.lower():
            channels += 'PRIO, '
        if channels == '':
            channels = 'Not Given, '
        df['test_channel'].append(channels[0 : len(channels) - 2])
        #sample_wells = plate.df.loc[~plate.df['barcode'].isin(self.globals['NON_PATIENT_CODES'])]
        df['patient_samples'].append(plate.info['Total Samples'][0])
        pos = len(plate.df.loc[(plate.df['nFAM'] >= self.thresholds['POSITIVE_THRESHOLD']) &
                               (plate.df['ROX'] >= self.thresholds['ROX_LIMIT']) &
                               ~(plate.df['barcode'].isin(self.globals['NON_PATIENT_CODES']))])
        df['positives'].append(pos)
        df['positive_wells'].append('-')
        df['vic_pos_wells'].append('-')
        df['vic_fails'].append(plate.info['VIC Failures'][0])
        df['accu_fails'].append(len(plate.df.loc[(plate.df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']) &
                                                 (plate.df['barcode'] == 'Con') &
                                                 (plate.df['well'].isin(self.globals['ACCUPLEX_WELLS'])) &
                                                 (plate.df['ROX'] >= self.thresholds['ROX_LIMIT'])]))
        df['poscon_fails'].append(len(plate.df.loc[(plate.df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD']) &
                                                 (plate.df['barcode'] == 'Con') &
                                                 (plate.df['well'].isin(self.globals['QNOS_WELLS'])) &
                                                 (plate.df['ROX'] >= self.thresholds['ROX_LIMIT'])]))
        df['negcon_fails'].append(len(plate.df.loc[(plate.df['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']) &
                                                 (plate.df['barcode'] == 'Con') &
                                                 (plate.df['well'].isin(self.globals['NEGCON_WELLS']) &
                                                 (plate.df['ROX'] >= self.thresholds['ROX_LIMIT']))]))
        if df['patient_samples'][-1] > 0:
            df['pos_rate'].append(plate.info['Positives'][0].split('(')[1].replace(')', ''))
        else:
            df['pos_rate'].append('0')
        if last_plate_buffer:
            carry_overs = f.detect_carryover(plate_pos, plate_vic, plate_plods, previous_fam, previous_vic)
        else:
            carry_overs = ('-', '-', '-')
        df['pos_punch'].append(carry_overs[0])
        df['vic_punch'].append(carry_overs[1])
        df['plod_punch'].append(carry_overs[2])
        
        return df        
          
    def buffer_summary(self):
        """
        Builds a buffer summary for the batch of plates being analysed
        
        Returns
        -------
            A pd.DataFrame in the form of a buffer summary table containing the data for this plate batch's buffer summary
        """
        # These lists will form the columns for the buffer summary dataframe:
        if not self.globals['BUFFER_SUMMARY']:
            return pd.DataFrame({'Buffer summary disabled': []})
        df = dict(plates = list(self.plates.keys()),
            plate_type = [],
            read_date = [],
            test_channel = [],
            patient_samples = [],
            positives = [],
            positive_wells = [],
            plods = [],
            plod_wells = [],
            vic_fails = [],
            vic_pos_wells = [],
            rox_failures = [],
            accu_fails = [],
            negcon_fails = [],
            poscon_fails = [],
            pos_rate = [],
            pos_punch = [],
            plod_punch = [],
            vic_punch = [])
        
        # These will be used to keep track of the positions of positives on previous plates:
        previous_fam = []
        previous_vic = []
        last_plate_buffer = False
        
        for array_code in self.plates:
            plate = self.plates[array_code]
            plate_pos = plate.df.loc[plate.df['nFAM'] >= self.thresholds['POSITIVE_THRESHOLD']]['well']
            plate_plods = plate.df.loc[(plate.df['nFAM'] >= self.thresholds['NEGATIVE_THRESHOLD']) & 
                                      ( plate.df['nFAM'] < self.thresholds['POSITIVE_THRESHOLD'])]['well']
            pos_vic = plate.df.loc[plate.df['nVIC'] >= self.thresholds['nVIC_THRESHOLD']]['well']
            df['plods'].append(len(plate_plods))
            df['plod_wells'].append(str(list(plate_plods)).replace('[', '').replace(']', '').replace("'", ''))
            df['rox_failures'].append(len(plate.df.loc[plate.df['ROX'] < plate.thresholds['ROX_LIMIT']]))
            
            if plate.pool == None:
                df = self._summary_buffer(df, plate_pos, pos_vic, plate_plods, previous_fam, previous_vic)
                last_plate_buffer = True
                
            else:
                df = self._summary_patient(df, plate, plate_pos, pos_vic, plate_plods, previous_fam, previous_vic, last_plate_buffer)
                last_plate_buffer = False
                
            df['read_date'].append(plate.date[0:10].replace(':', '/') + ' ' + plate.date[11:16])
            previous_fam = list(plate_pos)
            previous_vic = list(pos_vic)
        df = pd.DataFrame(df)
        df.rename({
            'plates' : 'Plate', 'plate_type' : 'Type', 'read_date' : 'Date', 'test_channel' : 'Channel',
            'patient_samples' : 'Num Samples', 'positives' : 'Positives', 'positive_wells' : 'Pos Wells',
            'plods' : 'PLODs', 'plod_wells' : 'PLOD Wells', 'vic_fails' : 'VIC Fails',
            'vic_pos_wells' : 'VIC Positives', 'rox_failures' : 'Low ROX', 'accu_fails' : 'Accuplex Fails',
            'negcon_fails' : 'Negcon Fails', 'poscon_fails' : 'Qnos Fails', 'pos_rate' : 'Patient Positivity', 
            'pos_punch' : 'Pos Punch', 'plod_punch' : 'Pos to PLOD', 'vic_punch' : 'VIC Punch'
            }, axis = 1, inplace = True)
        print('\nBuffer summary complete\n')
        return df
    
    def run_analysis(self, test = False):
        """
        Builds the HTML output file by iterating through all the plates and using their methods to append tabs to the HTML output.
        It then writes this output to a file and names it according to the highest and lowest array codes in the batch of plates
        """
        for plate in self.plates:
            plate_obj = self.plates[plate]
            print(plate)
            plate_str = str(plate)
            
            btn_str = str(plate)
            if self.cur == None:
                btn_str = f'<span style = "color:#1c20ed">{btn_str}</span>'
                plate_str += ' (offline)'
            else:
                if plate_obj.pool == None:
                    btn_str = f'<span style = "color:#00cc00">{btn_str}</span>'
                    plate_str += ' (possible buffer)'
                if plate_obj.check_if_prio():
                    btn_str = f'<span style = "color:#e60000">{btn_str}</span>'
                    plate_str += ' (priority)'
                if plate_obj.check_if_vip():
                    btn_str = f'<span style = "color:#DC9202">{btn_str}</span>'
                    plate_str += ' (VIP)'
                
            self.html = self.html.replace('£new_plate_button£', self.globals['BUTTON_STRING'].replace(
                '£plate£', str(plate)).replace('£btn_txt£', btn_str))
            
            if (plate_obj.pool,) in self.restamped:
                plate_str += ' (<span style = "color:#e60000">restamped</span>)'
            
            self.html = self.html.replace('£new_plate_tab£', plate_obj.create_tab(plate_str))
            self.plates[plate].df.to_csv('temp.csv')
        self.html = self.html.replace('£new_plate_button£', '').replace('£new_plate_tab£', '')  # Clean up the HTML string
        
        array_codes = [x for x in self.plates.keys()]
        self.html = self.html.replace('£background_colour£', self.globals['BACKGROUND_COLOUR'])
        self.html = self.html.replace('£title£', str(min(array_codes)) + ' - ' + str(max(array_codes)))
        summary = DINO_ART
        if not type(self.summary) == str:
            summary = self.summary.to_html(index = False)
        self.html = self.html.replace('£plotlyjs£', self.globals['PLOTLY_JS'])
        self.html = self.html.replace('£buffer_summary£', summary)
        if not test:
            with open(f'.//Output//{str(min(array_codes))} - {str(max(array_codes))}.html', 'w', encoding = 'utf-8') as file:
                file.write(self.html)  # Write the HTML output
            if self.globals['SAVE_ANALYSIS']:
                with open(f"//strjupiterflproduks01.file.core.windows.net//limsextract//poolHelper//Archive//{str(min(array_codes))} - {str(max(array_codes))}.html",
                          'w', encoding = 'utf-8') as file:
                    file.write(self.html)
        else:
            return self.html
            