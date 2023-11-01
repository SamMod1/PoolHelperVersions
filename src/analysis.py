import os
import io
import numpy as np
import pandas as pd
import src.plate as pl
import src.functions as f
from datetime import datetime, timedelta


QUADRANTS = ('Q1', 'Q2', 'Q3', 'Q4')
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
    def __init__(self, version, first_array, glob, thresholds, cur, p_thresholds, alpha, n_sims, admin = False, from_files = False, 
                 mirrorless = False, filepath = './/Araya Files//'):
        self.cur = cur
        self.alpha = alpha
        self.simulations = n_sims
        self.admin = admin
        self.mirrorless = mirrorless
        self.globals = glob
        self.html = self.globals['HTML_FIRST_TAB']
        self.html = self.html.replace('£version£', version)
        self.thresholds = thresholds
        self.p_thresholds = p_thresholds
        self.plates = self.pipe(first_array, filepath = filepath, from_files = from_files)
        self.date = datetime.strptime(self.plates[list(self.plates.keys())[0]].date[0:10], '%Y:%m:%d')
        print('Finding restamps...')
        self.restamped = f.restamp_finder(self.date - timedelta(days = 3), self.date + timedelta(days = 1), self.cur)
        self.set_thresholds()
        pools = tuple([x.pool for x in list(self.plates.values()) if x.pool != None])
        pools_str = str(pools)
        if len(pools) == 1:
            pools_str = pools_str.replace(',', '')
        query = f"""select JOB_NAME, substr(SAMPLE_BARCODE, 1, 3), PLATE_COORDINATE from VGSM.SAMPLE 
            where JOB_NAME in {pools_str}"""
        
        barcode_dict = {}
        con_wells_letter = self.globals['ACCUPLEX_WELLS'] + self.globals['QNOS_WELLS'] + self.globals['NEGCON_WELLS']
        if self.cur == None:
            barcode_matrix = np.array([['Sample' for _ in range(24)] for _ in range(16)]) #f.extract_barcodes(str(plate), CONNECTION).to_numpy()  # barcode preffixes
            con_wells = tuple([(LETTERS.index(x[0]), int(x[1:]) - 1) for x in con_wells_letter])
            for x in con_wells:
                barcode_matrix[x] = 'Con'
            for plate in self.plates:
                self.plates[plate].barcodes_from_matrix(barcode_matrix)
                self.plates[plate].data_as_df()
                self.plates[plate].create_platemaps()
                self.plates[plate].plate_info()
            self.summary = 'Unavailable'
        else:
            if False:#try:
                barcodes = f.lims_query(query, cur)
                for pool in pools:
                    barcode_dict[pool] = []
                for sample in barcodes:
                    if sample[2] in con_wells_letter:
                        if len(sample[1]) > 0:
                            sample = (sample[0], 'Con', sample[2])
                    barcode_dict[sample[0]].append(sample)
            if True:#except cx_Oracle.DatabaseError:
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
                araya = f.get_araya(plate, self.cur)
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
        
    def _plate_read(self, filename, array_code, pool, filepath = './/Araya Files//') -> dict:
        """
        Takes an araya file from LIMS as a bytes object and reads all of the data into an data frame. Most of this code was written by Graham Hill.
        The function also writes the araya file as a csv file to the specified filepath.
        
        Parameters:
            file: An araya file represented as a bytes object obtained directly from the LIMS database.
            df: A dictionary representing a data frame. This should have the following keys:
                'readDate', arrayCode', 'FAM', 'VIC', 'ROX', 'Quadrant', 'x384well', 'x384row', 'x384col', 'x96row', 'x96col', 'x96well', 
                'TapeID', 'n_FAM', 'n_VIC'.
            filepath: The filepath in which to write the downloaded araya files.
            
        Returns:
            A version of the dictionary df, which has had all of the araya file's data appended to it.
        """
        if type(filename) == str:
            with open(filepath + filename, 'r') as file:
                file = file.readlines()
        else:
            b_file = io.BytesIO(filename.read()).readlines()
            #print(b_file)
            file = []
            for b_line in b_file:
                line = b_line.decode()
                file.append(line)
        rawdat = file[1].split('-')[1]
        date = rawdat[0:4]+":"+rawdat[4:6]+":"+rawdat[6:8]+":"+rawdat[8:10]+":"+rawdat[10:12]+":"+rawdat[12:14]
        active = None
        plate = pl.Plate(pool, array_code, self.globals, self.thresholds, self.p_thresholds, date, self.cur, self.alpha, self.simulations)
        FAM = []
        VIC = []
        ROX = []
        for line in file:
            line = line.replace('\n', '').replace('\r', '')
            #print(line + '//end//')
            #file is csv, split on comma
            col = line.split(",")
            #print(col)
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
                    plate.read_date = date
                elif "Code" == col[0]:
                    code = col[1]	
                    plate.array_code = code[-6:]
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
                plate[col + row] = pl.Sample(int(float(FAM[idx])), int(float(VIC[idx])), int(float(ROX[idx])))
                idx += 1
        
        # Write out the file as a .csv file incase the data scientist wants is:
        if not type(filename) == str:
            with open(filepath + rawdat + '_' + code.replace('.', '-') + '.csv', 'wb') as f:
                f.writelines(b_file)
                #for line in file:
                #    f.write(line[0:len(line) - 1])
        return plate

    def _get_files(self, first : str):
        """
        Finds and downloads any araya files in LIMS which are within the same batch as the first Tape ID which is supplied 
        to the fuction
        
        Parameters
        ----------
            first : str
                Any array code in the batch of plates to be downloaded (doesn't actually have to be the first in the batch)
            cur : cx_Oracle cursor object
                A cursor object from a connection to the LIMS mirror datbase
        
        Returns
        -------
            A list of tuples which contain the array code in the 0th index and the file itself (as a cx_Oracle.LOB object) in
            the 1st index
        """
        first = int(first)
        arrays = [x for x in range(first - 16, first + 16)]  # Generates all possible array codes in the batch
        insert_str = ''
        for array in arrays:
            str_array = str(array) + '.csv'
            while True:
                if len(str_array) >= 10:
                    break
                str_array = '0' + str_array
            insert_str += f"SWEEPER_LOG.ORIGINAL_FILENAME like '%{str_array}' or "  # Add possible array codes to the query
        insert_str = insert_str[0:-4]

        query = f"""
        select substr(SWEEPER_LOG.ORIGINAL_FILENAME, 43),BLOB_VALUES.BLOB_FIELD from SWEEPER_LOG inner join BLOB_VALUES on
        SWEEPER_LOG.ARCHIVED_FILE_BLOB = BLOB_VALUES.BLOB_ID where {insert_str}
        """
        all_files = f.lims_query(query, self.cur)
        all_arrays = [int(x[0][0:6]) for x in all_files]
        #print(arrays)

        # This code filters out any arrays which are not in the same batch as the given array
        wanted_arrays = []
        lower = arrays[:16]
        lower.reverse()
        for array in lower:
            if array in all_arrays:
                wanted_arrays.append(all_files[all_arrays.index(array)])
                
            else:
                break
            
        higher = arrays[16:]
        for array in higher:
            if array in all_arrays:
                wanted_arrays.append(all_files[all_arrays.index(array)])
            else:
                break

        return sorted(wanted_arrays, key=lambda x: x[0], reverse=False)
    
    def pipe(self, first : str, filepath = './/Araya Files//', from_files = False) -> dict:
        """
        This should probably be a method of the analysis class
        Creates a dictionary from the raw data in the araya files located in the filepath. This can then be turned into a DataFrame.
        
        Parameters
        ----------
            first : str
                The tape ID which is in the batch the user wants to analyse.
            glob : dict
                Contains the global variables for Pool Helper which are stored encrypted on the shared drive
            thresholds : dict
                Contains the thresholds for the current araya
            cur: A cx_Oracle cursor object connected to the LIMS mirror database.
            filepath : str
                The location in which to save the array files which this function will download
                NOTE: All files here will be overwritten if from_files is set to False
            from_files : bool
                Whether to run the function from araya files in the filepath directory. If False, this function will download 
                files from the LIMS mirror using the first array code supplied to the function
        
        Returns
        -------
            A dictionary with the keys:
                'readDate', arrayCode', 'FAM', 'VIC', 'ROX', 'Quadrant', 'x384well', 'x384row', 'x384col', 'x96row', 'x96col', 'x96well', 
                'TapeID', 'n_FAM', 'n_VIC'
        
        This fuction is made from Graham's code in his 'PaulPipe script.
        """
        if not from_files:
            for file in os.listdir(filepath):
                os.remove(filepath + file)  # Deletes all arayas still in the araya files directory
            files = self._get_files(first)
            plates = {}
            #extra bit for terminal
        
            for file in files:
                pool = f.get_pool(file[0][:6], self.cur)
                plates[file[0][:6]] = self._plate_read(file[1], int(file[0][:6]), pool)
        else:
            plates = {}
            plate_lst = []
            for each_file in os.listdir(filepath):
            #eliminate non-csv
               if each_file.endswith(".csv"):
            	#eliminate file-level duplicates
                if " " in each_file:
                    pass
                else:
                    if each_file[-10:-4] in plates.keys():
                        pass
                    else:
                        pool = f.get_pool(each_file[-10:-4], self.cur)
                        plate_lst.append([each_file, pool])
               else:
               	pass
            plate_lst = sorted(plate_lst, key=lambda x: x[-10:-4], reverse=False)
            for each_file in plate_lst:
                plates[each_file[0][-10:-4]] = self._plate_read(each_file[0], int(each_file[0][-10:-4]), each_file[1], filepath = filepath)
        return plates
          
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
                
            self.html = self.html.replace('£new_plate_button£', self.globals['BUTTON_STRING'].replace(
                '£plate£', str(plate)).replace('£btn_txt£', btn_str))
            
            if (plate_obj.pool,) in self.restamped:
                plate_str += ' (<span style = "color:#e60000">restamped</span>)'
            
            self.html = self.html.replace('£new_plate_tab£', plate_obj.create_tab(plate_str))
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
        else:
            return self.html
        