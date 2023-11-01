import numpy as np
import BackgroundTasks.PlateAnalysis.classes.analysis_functions as func
from poolFinder.models import ArayaThresholds, Sample, AnalysedPlate, PlateSummary
from poolFinder.functions.config_parse import CONFIG
from poolFinder.functions.app_functions import round_fixed
import pandas as pd
from .sample import Sample as SampleClass
from datetime import datetime


QUADRANTS = ('Q1', 'Q2', 'Q3', 'Q4')
QUAD_OFFSETS = {'Q1' : [0, 0], 'Q2' : [0, 1], 'Q3' : [1, 0], 'Q4' : [1, 1]}
LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
WELLS = {
    'Q1' : ('A01', 'C03', 'E05', 'G07', 'I09', 'K11', 'M13', 'O15'),
    'Q2' : ('A02', 'C04', 'E06', 'G08', 'I10', 'K12', 'M14', 'O16'),
    'Q3' : ('B01', 'D03', 'F05', 'H07', 'J09', 'L11', 'N13', 'P15'),
    'Q4' : ('B02', 'D04', 'F06', 'H08', 'J10', 'L12', 'N14', 'P16'),
    }



class Plate:
    def __init__(self, array_code, pool):
        self.array_code = array_code
        self.pool = pool
        self.sample_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        self.instruments = None
        self.araya = None
        self.thresholds = None
        self.read_date = None
        self.df = None
        self.matrices = None
        self.roxbox = None
        self.escalated = False
        self.is_prio = False
        self.is_vip = False
        self.is_repooled = False
        self.is_restamped = False
        self.comments = 'Unavailable'
        self.formatted_info = {'plate_info' : 'Unavailable', 'escalations' : '', 'comments' : 'Unavailable'}
        self.escalations = []
        self.elutes = []
        self.unique_platename = None

        mm_fam_vic = CONFIG['MM_RULE_FAM_TO_VIC_LIMITS'].split(', ')
        stripe_limit = CONFIG['STRIPE_LIMIT'].split(', ')
        sop_plod_limit = CONFIG['SOP_PLOD_LIMIT'].split(', ')
        sop_rox_fail_limit =CONFIG['SOP_ROX_FAIL_LIMIT'].split(', ')
        sop_nvic_escalation_limt = CONFIG['SOP_nVIC_ESCALATION_LIMIT'].split(', ')
        x96_control_wells = CONFIG['x96_CONTROL_WELLS'].split(' ')
        for idx in range(len(x96_control_wells)):
            well = x96_control_wells[idx].split(',')
            well = (int(well[0]), int(well[1]))
            x96_control_wells[idx] = well
        self.globals = dict( # Pulls out the config variables we'll need and store them in a dictionary
            ACCUPLEX_WELLS = CONFIG['ACCUPLEX_WELLS'].split(', '),
            QNOS_WELLS = CONFIG['QNOS_WELLS'].split(', '),
            NEGCON_WELLS = CONFIG['NEGCON_WELLS'].split(', '),
            NON_PATIENT_CODES = CONFIG['NON_PATIENT_CODES'].split(', '),
            MM_RULE_MIN_ROX_MODIFIER = float(CONFIG['MM_RULE_MIN_ROX_MODIFIER']),
            MM_RULE_MAX_nVIC_MODIFIER = float(CONFIG['MM_RULE_MAX_nVIC_MODIFIER']),
            MM_RULE_FAM_VIC_LOW = float(mm_fam_vic[0]),
            MM_RULE_FAM_VIC_HIGH = float(mm_fam_vic[1]),
            STRIPE_LIMIT = (float(stripe_limit[0]), float(stripe_limit[1])),
            STIPE_CHECK_LIMIT = float(CONFIG['STIPE_CHECK_LIMIT']),
            SOP_PLOD_LIMIT = (float(sop_plod_limit[0]), sop_plod_limit[1]),
            SOP_ROX_FAIL_LIMIT = (float(sop_rox_fail_limit[0]), sop_rox_fail_limit[1]),
            SOP_nVIC_ESCALATION_LIMIT = (float(sop_nvic_escalation_limt[0]), sop_nvic_escalation_limt[1]),
            x96_CONTROL_WELLS = x96_control_wells,
            BACKGROUND_COLOUR = CONFIG['BACKGROUND_COLOUR'],
            GRAPH_LINE_SIZE = int(CONFIG['GRAPH_LINE_SIZE']),
            PRIO_CODES = CONFIG['PRIO_CODES'].split(', ')
        )

    def __getitem__(self, coordinates : str):
        """Gets the item stored at the coordinates in the sample_matrix"""
        true_coords = [LETTERS.index(coordinates[0]), int(coordinates[1:]) - 1]
        return self.sample_matrix[true_coords[0]][true_coords[1]]
    
    def __setitem__(self, coordinates : str, new_value):
        """Sets the item stored at the coordinates in the sample_matrix to the new_value"""
        true_coords = [LETTERS.index(coordinates[0]), int(coordinates[1:]) - 1]
        self.sample_matrix[true_coords[0]][true_coords[1]] = new_value

    def set_thresholds(self):
        """
        Sets the thresholds for positivity for this plate determined by the plate's araya (self.araya) and the araya thresholds
        stored in the Pool Helper database
        """
        if self.instruments == None:
            raise NameError(f"Plate {self.array_code}'s instruments have not been set yet")
        self.araya = self.instruments['Araya']
        thresholds = ArayaThresholds.objects.filter(araya = self.araya).first()
        self.thresholds = dict(
            POSITIVE = thresholds.positive,
            NEGATIVE = thresholds.negative,
            nVIC = thresholds.nvic,
            LOW_ROX = thresholds.low_rox,
            HIGH_ROX = thresholds.high_rox
        )
    
    def set_araya_data(self, file):
        """
        Modified from a function origionally created by Graham Hill
        Extracts the plate's data form an araya file and saves it as a numpy array with the dimensions of a 384-well plate
        Each sample is saved into this array as an instance of the Sample class (the barcode prefix is not set here however)

        PARAMETERS:
            file: str - A string containing the raw data in an araya file (comma-deliminated format). This file must have the
                        exact same format as an araya file as it comes from the araya (if the file has been saved by excel
                        at any time this can cause issues)
        """
        rawdat = file[1].split('-')[1]
        date = rawdat[0:4]+":"+rawdat[4:6]+":"+rawdat[6:8]+":"+rawdat[8:10]+":"+rawdat[10:12]+":"+rawdat[12:14]
        active = None
        FAM = []
        VIC = []
        ROX = []
        for line in file:
            line = line.replace('\n', '').replace('\r', '')
            col = line.split(",")
            if len(col) > 1:
                if len(col) == 26 and active == "FAM":
                    #grab the relevant fluo values as a list
                    row = col[1:25]
                    #append the list to the FAM list
                    FAM.extend(row)
                #Repeat for VIC and ROX
                elif len(col) == 26 and active == "VIC":
                    row = col[1:25]
                    VIC.extend(row)
                elif len(col) == 26 and active == "ROX":
                    row = col[1:25]
                    ROX.extend(row)	
                elif "Date" == col[0]:
                    rawdat = col[1].strip("-")
                    date = rawdat[0:4]+":"+rawdat[4:6]+":"+rawdat[6:8]+":"+rawdat[8:10]+":"+rawdat[10:12]+":"+rawdat[12:14]
                    self.read_date = date
                #trigger for reading the FAM table and init FAM list
                elif "FAM" == col[1]:
                    active = "FAM"
                #if the line is long enough to have fluo values and FAM is on, values go to FAM
                elif "VIC" == col[1]:
                    active = "VIC"
                elif "ROX" == col[1]:
                    active = "ROX"
                #So all the FAM, VIC and ROX fluo values are stored by row and column in a list of lists
        idx = 0
        for col in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"):
            for row in [str(x) for x in range(1, 25)]:
                self[col + row] = SampleClass(int(float(FAM[idx])), int(float(VIC[idx])), int(float(ROX[idx])))
                idx += 1

    def set_barcodes(self, barcodes : list):
        """
        Sets the barcode of every Sample on the plate to be the values in the given list
        
        PARAMETERS:
        barcodes : list
            A list of tuples containing all of the barcodes for the plate in the format: (pool plate id, barcode, well)
        """
        for sample in barcodes:
            well = sample[2]
            if well[1] == '0':  # Removes the leading zeros is present
                well = well[0] + well[2]
            self[well].set_barcode(sample[1])

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
     
    def _create_matrices(self):
        """
        Sets a dictionary containing 11 numpy matrices to the variable self.matrices
        
        SETS:
            list containing database Sample objects. Together these Sample objects contain all the data for the plate

            dict containing the following matrices:
                result_matrix: A matrix representing the platemap of results based on the nFAM value. 0 = Negative, 1 = PLOD, 2 = Positive
                flag_matrix: A matrix of warnings for wells. Warnings include: PLOD, HI PLOD, VIC FAIL, Pos fail, Neg fail, etc...
                barcode_matrix: A platemap of the barcode preffixes of each sample on the plate
                wells_matrix: A map of all the wells on the plate
        """
        result_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        flag_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        barcode_matrix = np.array([[None for _ in range(24)] for _ in range(16)])
        wells_matrix = np.array([[None for _ in range(24)] for _ in range(16)])

        list_of_samples = []
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
                barcode = sample['barcode'] 
                barcode_matrix[row, col] = barcode
                fam = sample['FAM'] #fam_matrix[row, col] = sample['FAM']
                vic = sample['VIC'] #vic_matrix[row, col] = sample['VIC']
                rox = sample['ROX'] #rox_matrix[row, col] = sample['ROX']

                if self.thresholds['POSITIVE'] - 0.05 <= sample['nFAM'] < self.thresholds['POSITIVE']:
                    nfam = round_fixed(self.thresholds['POSITIVE'] - 0.1, 1)
                elif self.thresholds['NEGATIVE'] - 0.05 <= sample['nFAM'] < self.thresholds['NEGATIVE']:
                    nfam = round_fixed(self.thresholds['NEGATIVE'] - 0.1, 1)
                else:
                    nfam = round_fixed(sample['nFAM'], 1)

                if self.thresholds['nVIC'] - 0.05 <= sample['nVIC'] < self.thresholds['nVIC']:
                    nvic = round_fixed(self.thresholds['nVIC'] - 0.1, 1)
                else:    
                    nvic = round_fixed(sample['nVIC'], 1)

                if sample['nFAM'] < self.thresholds['NEGATIVE']:
                    result_matrix[row, col] = 0
                elif self.thresholds['NEGATIVE'] <= sample['nFAM'] < self.thresholds['POSITIVE']:
                    result_matrix[row, col] = 1
                else:
                    result_matrix[row, col] = 2

                sample_well = LETTERS[row] + str(col + 1)
                warning = 'None'
                if sample['ROX'] < self.thresholds['LOW_ROX']:
                    if sample['barcode'] == 'Con':
                        if sample_well in self.globals['ACCUPLEX_WELLS']:
                            warning = 'ROX accu'
                        elif sample_well in self.globals['QNOS_WELLS']:
                            warning = 'ROX qnos'
                        elif sample_well in self.globals['NEGCON_WELLS']:
                            warning = 'ROX negcon'
                    elif sample['barcode'] in self.globals['NON_PATIENT_CODES']:
                        if sample['barcode'] == 'SPA':
                            warning = 'SPA ROX'
                        else:
                            warning = 'ENV ROX'
                    else:
                        warning = 'ROX fail'
                elif sample['barcode'] == 'Con':  # I.e if control
                    if sample_well in self.globals['ACCUPLEX_WELLS'] + self.globals['QNOS_WELLS']:  # I.e if poscon
                        if sample_well in self.globals['ACCUPLEX_WELLS']:
                            if sample['nVIC'] >= self.thresholds['nVIC']:
                                warning = 'VIC accu'  # This warning is used elsewhere in code, if it is changed, also change that line
                        if sample['nFAM'] < self.thresholds['POSITIVE']:
                            warning = 'Pos fail'  # This warning is used elsewhere in code, if it is changed, also change that line
                    elif sample_well in self.globals['NEGCON_WELLS'] and sample['nFAM'] >= self.thresholds['NEGATIVE']:
                        warning = 'Neg fail'  # This warning is used elsewhere in code, if it is changed, also change that line
                elif sample['barcode'] in self.globals['NON_PATIENT_CODES']:  # If has no associated barcode
                    if not sample['barcode'] == 'SPA':
                        if sample['nFAM'] >= self.thresholds['NEGATIVE']:
                            warning = 'Contam'  # Can we be sure that barcodeless wells should always be negative?
                else:  # I.e if patient sample
                    if sample['nFAM'] < self.thresholds['NEGATIVE']:
                        if sample['nVIC'] >= self.thresholds['nVIC']:
                            if (sample['ROX'] >= self.thresholds['HIGH_ROX'] + self.globals['MM_RULE_MIN_ROX_MODIFIER'] and 
                                self.thresholds['nVIC'] <= sample['nVIC'] < self.thresholds['nVIC'] + 
                                self.globals['MM_RULE_MAX_nVIC_MODIFIER'] and self.globals['MM_RULE_FAM_VIC_LOW']
                                < sample['FAM'] / sample['VIC'] < self.globals['MM_RULE_FAM_VIC_HIGH']):  # Detects MM-only signals
                                warning = 'MM-only'  # This might falsely flag some wells, but warnings should always be reviewed by someone anyway
                        else:  # I.e if nFAM and nVIC is negative
                            warning = 'VIC fail'
                    elif sample['nFAM'] < self.thresholds['POSITIVE'] - 1:
                        warning = 'PLOD'
                    elif sample['nFAM'] < self.thresholds['POSITIVE']:
                        warning = 'HI PLOD'
                flag_matrix[row, col] = warning
                wells_matrix[row, col] = sample_well
                flags.append(warning)
                list_of_samples.append(Sample(
                    plate = None,
                    x384_well = sample_well,
                    fam = fam,
                    vic = vic,
                    rox = rox,
                    nfam = nfam,
                    nvic = nvic,
                    flag = warning,
                    barcode = barcode
                    ))
        self.df['Flags'] = flags
        self.df['Quadrant'] = quadrants
        return list_of_samples, dict(
            result_matrix = result_matrix, 
            flag_matrix = flag_matrix, 
            barcode_matrix = barcode_matrix, 
            wells_matrix = wells_matrix
            )
                    
    def _quadrant_statistics(self, quadrant_matrices):
        """
        Takes a dictionary containing containing a matrix of the results of a single quadrant (result_matrix). Counts the
        total number of patient samples and positive patient samples in this matrix

        PARAMETERS:
            quadrant_matrices: dict - contains at least one numpy array (8 by 12) with the results in (0=neg, 1=plod, 2=pos)
        
        RETURNS:
            dict - The same dict as was passed to the function, now with two new values (int) under the keys:
                   'total' - the total number of patient samples on the plate
                   'pos' - the total number of positive patient samples on the plate
        """
        for row in range(quadrant_matrices['barcode_matrix'].shape[0]):
            for col in range(quadrant_matrices['barcode_matrix'].shape[1]):
                if not quadrant_matrices['barcode_matrix'][row, col] in self.globals['NON_PATIENT_CODES']:
                    quadrant_matrices['total'] += 1
                    if float(quadrant_matrices['result_matrix'][row, col]) == 2:
                        quadrant_matrices['pos'] += 1
        return quadrant_matrices

    def _detect_escalations_384(self, flag_matrix):
        """
        Detects if the plate needs to be escalated because it has too many RNaseP failures, ROX failures or PLODs and appends the escalation
        self.escalations
        """
        if (flag_matrix == 'VIC fail').sum() >= self.globals['SOP_nVIC_ESCALATION_LIMIT'][0]:
            self.escalations.append(f'{int(self.globals["SOP_nVIC_ESCALATION_LIMIT"][0])} or more RNaseP failures')
            self.escalated = True
        if (flag_matrix == 'ROX fail').sum() >= self.globals['SOP_ROX_FAIL_LIMIT'][0]:
            self.escalations.append(f'{int(self.globals["SOP_ROX_FAIL_LIMIT"][0])} or more ROX fails')
            self.escalated = True
        if (flag_matrix == 'PLOD').sum() >= self.globals['SOP_PLOD_LIMIT'][0]:
            self.escalations.append(f'{int(self.globals["SOP_PLOD_LIMIT"][0])} or more PLODs')
    
    def _detect_escalations_quadrant(self, matrices, quadrant):
        """Detects if the plate needs to be escalated because a failure has invalidated samples"""
        if np.isin(matrices['flag_matrix'], ('VIC accu', 'Pos fail', 'ROX qnos')).sum() >= 2:
            if 'VIC accu' in matrices['flag_matrix']:
                self.escalations.append(f'The qnostic has failed on {quadrant}, and the accuplex in the same quadrant contains RNaseP')
                self.escalated = True
            else:
                self.escalations.append(f'Both positive controls on {quadrant} have failed')
                self.escalated = True
        if 'Neg fail' in matrices['flag_matrix'] or 'ROX negcon' in matrices['flag_matrix']:
            brk = False
            for row in range(8):
                for col in range(12):
                    if not matrices['barcode_matrix'][row, col] in self.globals['NON_PATIENT_CODES']:
                        #if float(matrices['nfam_matrix'][row, col]) >= self.thresholds['POSITIVE']:
                        if matrices['result_matrix'][row, col] == 2:
                            self.escalations.append(f'Negcon fail on {quadrant} has invalidated samples')
                            self.escalated = True
                            brk = True
                            break
                if brk:
                    break

    def _detect_stripes(self, quadrant_matrices, wells_matrix, list_of_samples_for_db, quadrant):
        """
        Applies the rules for striping found in the service guidance to individual quadrants

        IF the positivity rate for patient samples on the plate is <= 22 (value changeable the config)
        AND there is a stripe of four adjacent horizontal wells or 5 adjacent vertical wells (also changable in config)
        THEN flags those wells with the flag: 'Stripe'
        """
        stripe_wells = []
        if quadrant_matrices['pos'] >= min(self.globals['STRIPE_LIMIT']):
            if (quadrant_matrices['pos'] / quadrant_matrices['total'] * 100) <= self.globals['STIPE_CHECK_LIMIT']:
                quadrant_matrices['flag_matrix'] = func.find_stripes(quadrant_matrices['result_matrix'], 
                                                                            quadrant_matrices['flag_matrix'], 
                                                                            #new_matrices[quadrant]['flag_numbers'],
                                                                            self.globals)
                if np.any(quadrant_matrices['flag_matrix'] == 'Stripe'):
                    stripes = np.where(quadrant_matrices['flag_matrix'] == 'Stripe')
                    for idx in range(len(stripes[0])):
                        stripe_wells.append(wells_matrix[stripes[0][idx] * 2 + QUAD_OFFSETS[quadrant][0], 
                                            stripes[1][idx] * 2 + QUAD_OFFSETS[quadrant][1]])
                        
        for sample in [x for x in list_of_samples_for_db if x.x384_well in stripe_wells]:
            sample.flag = 'Stripe'

        return list_of_samples_for_db

    def _find_esclations_and_stripes(self, matrices : dict, list_of_samples_for_db : list) -> dict:
        """
        Extracts the four quadrants from a dictionary of 384-well numpy matrices and returns the dictionary with these new matrices
        added into it. This method also checks for striping of positive samples on quadrants based on service guidance and alters the
        flag_matrix accordingly
        
        PARAMETERS:
            matrices: A dictionary containing various 384-well matrices, including a flag matrix
            
        RETURNS:
            dict containing all the matrices passed to the function with new keys: Q1, Q2, Q3 & Q4 who's values are dictionaries containing
            all the matrices for that individual quadrant
        """
        self._detect_escalations_384(matrices['flag_matrix'])
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
            new_matrices[quadrant] = self._quadrant_statistics(new_matrices[quadrant])

            list_of_samples_for_db = self._detect_stripes(
                new_matrices[quadrant], 
                new_matrices['384']['wells_matrix'],
                list_of_samples_for_db,
                quadrant)
                            
            self._detect_escalations_quadrant(new_matrices[quadrant], quadrant)

        return list_of_samples_for_db
    
    def plate_analysis(self):
        """
        Gathers the plate analaysis data and stores it in a way in which it can be easily inserted into the database
        Also generates some platemaps and looks for escalations and stripes
        """
        list_of_samples_for_db, matrices = self._create_matrices()
        self.sample_db_objects = self._find_esclations_and_stripes(matrices, list_of_samples_for_db)

    def get_lysis_and_elute_plates(self, response) -> dict:
        """
        Queries LIMS to find all of the lysis and elution plates associated with each quadrant on the plate.
        Note: there is a bug in LIMS which means this does not work for lysis plates which were made manually (i.e. not on the hamilton).
        
        PARAMETERS:
            response: A list of tuples containing data from JOB_HEADER showing which lysis and elution plates are associated with the pool plate.

        RETURNS:
            A dictionary containing lists with the lysis and elution plates for each quadrant and the Pool Plate.
            Also there are some empty fields initialised in this dictionary as well for the Nexar, Araya, Hydrocycler and 384 Hamilton the 
            plate was run on.
        """
        result = {'Pool plate' : self.pool, 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
                  'Q1' : ['',''], 'Q2' : ['',''], 'Q3' : ['',''], 'Q4' : ['','']}
        quadrants = ['Q1', 'Q2', 'Q3', 'Q4']
        for x in response:
            for quadrant in quadrants:
                if x[2] in WELLS[quadrant]:
                    if x[0] == None:
                        x = list(x)
                        x[0] = 'NoInact' + quadrant
                        result[x[0]] = 'NONE'
                    else:
                        result[x[0]] = None
                    if x[1] == None:
                        x = list(x)
                        x[1] = 'NoElute' + quadrant
                        result[x[1]] = {1: 'NONE', 2: 'NONE'}
                    else:
                        result[x[1]] = {}
                    self.elutes.append(x[1])
                    result[quadrant] = x[0:2]
                    quadrants.remove(quadrant)
                    break
            if len(quadrants) == 0:
                break

        return result

    def find_instruments(self, instruments, result):
        """
        Returns the pool plate as well as the nexar, araya, hydrocycler and 384 hamilton it was run on. It also returns the inactivation and
        elution plates relating to each quadrant.
        
        PARAMETERS:
            instruments: A list of tuples containing data from JOB_PARAMETER pertaining to which instruments each plate was run on.
            result: The returned result of a previous call of the method get_lysis_and_elute_plates.
        
        RETURNS:
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
        Sets self.info as a dictionary containing:
            Positive samples, number of patient PLODs and RNaseP failures across the whole plate and Q1, Q2, Q3, and Q4
        self.find_instruments must have been run prior to this method being run.
            
        WARNING
            The output of this is used later to build the buffer summary, if the format of the plate info is changed, the buffer
            Analysis.buffer_summary method might break
        """
        if self.pool:
            sub_df = self.df.loc[(self.df['ROX'] >= self.thresholds['LOW_ROX']) & 
                                ~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES']))]
            totals = {'total' : len(self.df.loc[~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES']))])}
        else:
            sub_df = self.df
            totals = {'total' : 0}

        total_pos = len(sub_df.loc[sub_df['nFAM'] >= self.thresholds['POSITIVE']])
        
        total_plod = len(sub_df.loc[(sub_df['nFAM'] >= self.thresholds['NEGATIVE']) &
                                        (sub_df['nFAM'] < self.thresholds['POSITIVE'])])
        
        total_neg = len(sub_df.loc[(sub_df['nFAM'] < self.thresholds['NEGATIVE']) & 
                                (sub_df['nVIC'] >= self.thresholds['nVIC'])])
        
        total_nvic_fails = len(sub_df.loc[(sub_df['nFAM'] < self.thresholds['NEGATIVE']) &
                                        (sub_df['nVIC'] < self.thresholds['nVIC'])])
        positives = [total_pos]
        plods = [total_plod]
        negs = [total_neg]
        nvic_fails = [total_nvic_fails]
        total_samples = [totals['total']]
        if self.pool:
            plate_location = ('384', 'Q1', 'Q2', 'Q3', 'Q4')
            for quadrant in QUADRANTS:
                totals[quadrant] = len(self.df.loc[~(self.df['barcode'].isin(self.globals['NON_PATIENT_CODES'])) & 
                                    (self.df['Quadrant'] == quadrant)])
                
                quad_df = sub_df.loc[sub_df['Quadrant'] == quadrant]
                quadrant_pos = len(quad_df.loc[quad_df['nFAM'] >= self.thresholds['POSITIVE']])
                positives.append(quadrant_pos)

                plods.append(len(quad_df.loc[(quad_df['nFAM'] >= self.thresholds['NEGATIVE']) &
                                            (quad_df['nFAM'] < self.thresholds['POSITIVE'])]))
                negs.append(len(quad_df.loc[(quad_df['nFAM'] < self.thresholds['NEGATIVE']) &
                                            (quad_df['nVIC'] >= self.thresholds['nVIC'])]))
                nvic_fails.append(len(quad_df.loc[(quad_df['nFAM'] < self.thresholds['NEGATIVE']) &
                                                (quad_df['nVIC'] < self.thresholds['nVIC'])]))
                total_samples.append(totals[quadrant])

            instrument_info = ['', self.instruments['Q1'][0], self.instruments['Q2'][0], self.instruments['Q3'][0], self.instruments['Q4'][0]]
            nexar = [self.instruments['Nexar'], self.instruments[self.instruments['Q1'][0]], self.instruments[self.instruments['Q2'][0]], 
                        self.instruments[self.instruments['Q3'][0]], self.instruments[self.instruments['Q4'][0]]]
            araya = [self.instruments['Araya'], self.instruments['Q1'][1], self.instruments['Q2'][1], self.instruments['Q3'][1], self.instruments['Q4'][1]]
            hydro = [self.instruments['Hydrocycler'], self.instruments[self.instruments['Q1'][1]][0], self.instruments[self.instruments['Q2'][1]][0],
                        self.instruments[self.instruments['Q3'][1]][0], self.instruments[self.instruments['Q4'][1]][0]]
            ham = [self.instruments['Hamilton'], self.instruments[self.instruments['Q1'][1]][1], self.instruments[self.instruments['Q2'][1]][1],
                        self.instruments[self.instruments['Q3'][1]][1], self.instruments[self.instruments['Q4'][1]][1]]
        else:
            nvic_fails = [0]
            plate_location = ['384']
            instrument_info = ['']
            nexar = ['']
            araya = ['']
            hydro = ['']
            ham = ['']
            
        self.high_plods = len(sub_df.loc[(sub_df['nFAM'] >= self.thresholds['POSITIVE'] - 1) &
                                    (sub_df['nFAM'] < self.thresholds['POSITIVE'])])

        self.info = {
                'plate_location' : plate_location,
                'positives' : positives,
                'plods' : plods,
                'negatives' : negs,
                'vic_fails' : nvic_fails,
                'total_samples' : total_samples,
                'inact_plate' : instrument_info,
                'nexar_or_dwp_ham' : nexar,
                'araya_or_elute' : araya,
                'hydrocycler_or_kf' : hydro,
                'df_or_384_ham' : ham
                }

    def rox_box(self):
        """Returns a dict with the Average ROX, ROX SD, ROX CV, num well with ROX < min rox threshold, num well with ROX > high rox threshold"""
        mean = self.df['ROX'].mean()
        sd = self.df['ROX'].std()
        low_rox_subset = self.df.loc[self.df['ROX'] < self.thresholds['LOW_ROX']]
        patient_low_rox = len(low_rox_subset.loc[~(low_rox_subset['barcode'].isin(self.globals['NON_PATIENT_CODES']))])
        self.roxbox = {'Average ROX' : int(round_fixed(mean, 0)), 'Standard Deviation' : int(round_fixed(sd, 0)), 
                'Total ROX < Threshold' : len(low_rox_subset), 'Patient ROX < Threshold' : patient_low_rox,
                'ROX >= Threshold' : len(self.df.loc[self.df['ROX'] >= self.thresholds['HIGH_ROX']])}
    
    def get_comments(self, comments_df) -> dict:
        """
        Returns a dictionary containing the comments on each plate which went into the pool plate, and the comments appended to the pool plate 
        itself (This is done becuase the official LIMS comment trail feature is broken, lol).
        self.instruments must have been run before this method is called
        
        PARAMETERS:
            plates: A dictionary containing all the various plate names in the following format:
                {
                'Q1': [<elution plate>, <inact plate>],
                'Q2': [<elution plate>, <inact plate>],
                'Q3': [<elution plate>, <inact plate>],
                'Q4': [<elution plate>, <inact plate>],
                'Pool':<pool plate>
                }
            cur: A cx_Oracle cursor which connects to the LIMS mirror database.
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
        self.comments = comments
    
    def format_info(self):
        """Formats plate info in a way which can be used by the Pool Helper program later"""
        if self.pool:
            self.formatted_info['escalations'] = func.format_escalations(self.escalations)
            self.formatted_info['comments'] = func.format_comments(self.comments, self.pool)

    def check_if_prio(self):
        """Returns True or False based on whether the plate is priority or not"""
        if 'priority' in self.formatted_info['comments'].lower() or np.any(np.isin(self.df['barcode'].unique(), self.globals['PRIO_CODES'])):
            return True
        return False
    
    def check_if_vip(self):
        """Returns True or False based on whether the plate is VIP or not"""
        if ' vip ' in ' ' + self.formatted_info['comments'].lower() + ' ' or '(vip)' in self.formatted_info['comments'].lower():
            return True
        return False

    def set_unique_platename(self):
        """
        Creates a unique platename for this batch with the format: 'plate.array_code'
        If a plate with that name already exists in the database it will append an appropriate number to the end of the name
        """
        self.unique_platename = self.array_code
        count = AnalysedPlate.objects.filter(array_code__startswith = self.array_code).count()
        if count:
            self.unique_platename += ' ' + str(count)

    def _save_samples_to_db(self, plate_db_object, batchname):
        """Saves each sample object to the Pool Helper database 'Sample' table"""
        for sample in self.sample_db_objects:
            sample.plate = plate_db_object
            sample.batch = batchname
        Sample.objects.bulk_create(self.sample_db_objects)

    def save_plate_info_to_db(self, plate_db_object):
        for idx in range(len(self.info['plate_location'])):
            table_row = PlateSummary()
            table_row.plate = plate_db_object
            table_row.plate_location = self.info['plate_location'][idx]
            table_row.positives = self.info['positives'][idx]
            table_row.plods = self.info['plods'][idx]
            table_row.negatives = self.info['negatives'][idx]
            table_row.vic_fails = self.info['vic_fails'][idx]
            table_row.total_samples = self.info['total_samples'][idx]
            table_row.inact_plate = self.info['inact_plate'][idx]
            table_row.nexar_or_dwp_ham = self.info['nexar_or_dwp_ham'][idx]
            table_row.araya_or_elute = self.info['araya_or_elute'][idx]
            table_row.hydrocycler_or_kf = self.info['hydrocycler_or_kf'][idx]
            table_row.df_or_384_ham = self.info['df_or_384_ham'][idx]
            
            table_row.save()

    def save_to_db(self, batch, user):
        """Saves this plate to the Pool Helper database 'AnalysedPlate' table"""
        in_ff = False
        pool = 'None'
        if self.pool:
            in_ff = True
            pool = self.pool

        analysed_plate = AnalysedPlate(
            array_code = self.unique_platename,
            in_ff = in_ff,
            pool = pool,
            date_in = datetime.now(),
            batch = batch,
            araya = self.araya,
            pl_comments = self.formatted_info['comments'],
            escalated = self.escalated,
            escalation_reason = self.formatted_info['escalations'],
            restamped = self.is_restamped,
            repooled = self.is_repooled,
            prio = self.is_prio,
            vip = self.is_vip,
            average_rox = self.roxbox['Average ROX'],
            rox_sd = self.roxbox['Standard Deviation'],
            total_rox_below_threshold = self.roxbox['Total ROX < Threshold'],
            patient_rox_below_threshold = self.roxbox['Patient ROX < Threshold'],
            rox_above_threshold = self.roxbox['ROX >= Threshold'],
            high_plods = self.high_plods
        )
        if user:
            analysed_plate.uploaded_by = user
        analysed_plate.save()

        self.save_plate_info_to_db(analysed_plate)
        
        self._save_samples_to_db(analysed_plate, batch.batch)
