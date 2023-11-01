import logging
from cx_Oracle import DatabaseError
import BackgroundTasks.PlateAnalysis.classes.analysis_functions as func
from BackgroundTasks.PlateAnalysis.new_plates_management_functions import decode_file
from poolFinder.models import PoolFinderConfig, Batch
import pandas as pd
from poolFinder.functions.config_parse import CONFIG
from .plate import Plate
import poolFinder.functions.app_functions as app_func
from datetime import datetime


LOGGER = logging.getLogger('django')
QUADRANTS = ('Q1', 'Q2', 'Q3', 'Q4')
QUAD_OFFSETS = {'Q1' : [0, 0], 'Q2' : [0, 1], 'Q3' : [1, 0], 'Q4' : [1, 1]}
LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")


class BatchAnalysis:
    def __init__(self, plate_arrays_and_pools, files = {}, araya = None):
        self.files = files
        self.array_codes = []
        self.pools = []
        self.any_in_lims = True
        self.araya = araya
        self.plates = []
        self.plates_dict = {}
        self.thresholds = {}
        self.summary = 'None'
        self.unique_batchname = ''
        for idx, plate in enumerate(sorted(plate_arrays_and_pools, key = lambda x: int(x[0]), reverse = False)):
            self.plates.append(Plate(plate[0], plate[1]))
            self.plates_dict[plate[0]] = self.plates[idx]
            self.array_codes.append(plate[0])
            self.pools.append(plate[1])

    def _get_files_query(self):
        """
        Works out all the possible array codes which could be in the current batch (goes based on the first array code
        in self.plates + and - 16) and downloads any araya files from the LIMS mirror sweeper which match these possible
        array codes.

        RETURNS:
            query - to get the output of the LIMS mirror query to get the araya files
        """
        insert_str = ''
        where_clause = CONFIG['GET_FILES_WHERE']

        possible_lowest_plate = int(self.array_codes[0]) - 15
        possible_highest_plate = int(self.array_codes[0]) + 15
        possible_plates = [str(x) + '.csv' for x in range(possible_lowest_plate, possible_highest_plate + 1)]

        for plate in possible_plates:
            if len(plate) < 10:
                plate = plate.replace('-', '')
                if len(plate) < 10:
                    plate = func.add_leading_zeros(plate, 10)
            insert_str += where_clause.replace('$array_code', plate)
        insert_str = insert_str[0:-4]

        query = CONFIG['GET_FILES_MAIN']
        query = query.replace('$where_clause', insert_str)

        return query

    def _remaining_pools_query(self, arrays_without_pools):
        query = CONFIG['POOL_QUERY']

        if len(arrays_without_pools) > 1:
            query = query.split(' $or$ ')[0].replace('$array_codes$', str(tuple(arrays_without_pools)))
        else:
            query = query.split(' $or$ ')[1].replace('$array_code$', arrays_without_pools[0])
        
        return query

    def _get_remaining_pools(self, arrays_without_pools):
        """
        For any array codes in the given list, this function queries the LIMS mirror to check if they also have a Pool plate

        RETURNS:
            dict - pool IDs matched to their array codes (which are the keys)
        """
        remaining_pools = {}
        query_response = app_func.lims_query(self._remaining_pools_query(arrays_without_pools))

        if query_response:
            for line in query_response:
                remaining_pools[line[0]] = line[1]

        return remaining_pools

    def _set_araya_data_from_files(self):
        """
        For each plate's file in self.files, creates a Plate object in the batch and sets it's data to match the file data
        using that plate's set_araya_data() method. This function also sets the araya thresholds for the batch to match the thresholds
        of the first plate in the batch and updates the self.pools list
        """
        if not self.files:
            return
        plates = []
        plates_dict = {}
        array_codes = []

        for array_code in sorted(self.files):
            if array_code in self.plates_dict:
                plate = self.plates_dict[array_code]
            else:
                plate = Plate(array_code, None)
            plate.set_araya_data(self.files[array_code])
            LOGGER.info('araya data set for ' + array_code)
            plates.append(plate)
            plates_dict[array_code] = plate
            array_codes.append(array_code)

        self.thresholds = plates[0].thresholds
        self.plates = plates
        self.plates_dict = plates_dict
        self.array_codes = array_codes
        self.pools = [x.pool for x in self.plates if x.pool]

    def _set_araya_data_from_lims(self):
        """
        Automatically download any files in the current batch from the LIMS mirror and sets each plate's data from the
        downloaded file. It also finds any plates in the batch which were not initially supplied to the batch when the
        batch was initialised
        """
        new_data = [[], [], {}]
        files_from_lims = sorted(app_func.lims_query(self._get_files_query()), key = lambda x: int(x[0][:6]))
        first_array_in_batch = int(self.array_codes[0])
        lower_files = [x for x in files_from_lims if int(x[0][:-4]) < first_array_in_batch]
        lower_files.reverse()
        upper_files = [x for x in files_from_lims if int(x[0][:-4]) > first_array_in_batch]

        arrays_to_keep = func.find_arrays_in_current_batch(first_array_in_batch, upper_files, lower_files)

        files_from_lims = [x for x in files_from_lims if x[0] in arrays_to_keep]
        arrays_without_pools = [x[0][:6] for x in files_from_lims if not x[0][:6] in self.array_codes]
        remaining_pools = {}
        if arrays_without_pools:
            remaining_pools = self._get_remaining_pools(arrays_without_pools)


        for line in files_from_lims:
            array = line[0][:-4]
            file = decode_file(line[1])
            if array in self.array_codes:
                plate = self.plates_dict[array]
                plate.set_araya_data(file)
            else:
                plate = Plate(array, None)
                if plate.array_code in remaining_pools:
                    plate.pool = remaining_pools[plate.array_code]
                plate.set_araya_data(file)
            new_data[0].append(plate)
            new_data[1].append(plate.array_code)
            new_data[2][plate.array_code] = plate
        self.plates = new_data[0]
        self.array_codes = new_data[1]
        self.plates_dict = new_data[2]
        self.pools = [x.pool for x in self.plates if x.pool]

    def set_plate_data(self):
        """
        If files have been supplied to the batch object, this function will use these to set the data for each plate in the batch.
        If no files were supplied it will automatically download the araya files from the LIMS mirror for the batch.
        It also finds any plates in the batch which were not initially supplied to the batch when the
        batch was initialised

        The function then gets the barcode preffixes for each sample on each plate in the batch and sends that data to each plate
        as well
        """
        if self.files:
            self._set_araya_data_from_files()
        else:
            self._set_araya_data_from_lims()

        pools = tuple([x.pool for x in self.plates if x.pool])
        if pools:
            pools_str = str(pools)
            if len(pools) == 1:
                pools_str = pools_str.replace(',', '')
            query = CONFIG['BARCODES_QUERY']
            query = query.replace('$pools', pools_str)
            barcodes = app_func.lims_query(query)
            barcode_dict = {}
            
            con_positions = PoolFinderConfig.objects.filter(option__in = ('ACCUPLEX_WELLS', 'QNOS_WELLS', 'NEGCON_WELLS')).all()
            con_positions = [CONFIG['ACCUPLEX_WELLS'], CONFIG['QNOS_WELLS'], CONFIG['NEGCON_WELLS']]
            con_wells_letter = []
            for x in con_positions:
                con_wells = x.split(', ')
                con_wells_letter.extend(con_wells)

            for pool in pools:
                barcode_dict[pool] = []
            for sample in barcodes:
                if sample[1] == CONFIG['BUFFER_PREFFIX']:
                    sample = (sample[0], '', sample[2])
                elif sample[2] in con_wells_letter:
                    if len(sample[1]) > 0:
                        sample = (sample[0], 'Con', sample[2])
                barcode_dict[sample[0]].append(sample)
            
            for plate in [x for x in self.plates if x.pool]:
                plate.set_barcodes(barcode_dict[plate.pool])
        else:
            self.any_in_lims = False

    def _lysis_elute_plates_query(self):
        """
        Queries the SAMPLE table. The query is set in the config in the database. This is the query at the moment:

        select JOB_NAME, LYSIS_PLATE, ELUTION_PLATE, PLATE_COORDINATE from SAMPLE where JOB_NAME in $pools and 
        PLATE_COORDINATE in $wells

        RETURNS:
            list - The response from the LIMS mirror as a list of tuples containing each row's data
        """
        query = CONFIG['LY_EL_QUERY']
        pools_str = str(tuple(self.pools))
        if len(self.pools) == 1:
            pools_str = pools_str.replace(',', '')
        query = query.replace('$pools', pools_str)
        return query

    def _instruments_query(self, plates):
        """
        Queries the JOB_PARAMETER table in LIMS where the job name is in plates (an iterable). This is the currently set query:

        select VALUE, JOB from JOB_PARAMETER where JOB in $plates

        RETURNS:
            list - The response from the LIMS mirror as a list of tuples containing each row's data
        """
        plates_str = str(tuple(plates))
        if len(plates) == 1:
            plates_str = plates_str.replace(',', '')
        query = CONFIG['INSTRUMENTS_QUERY']
        query = query.replace('$plates', str(plates_str))
        return query

    def set_plate_instruments(self):
        """
        First queries the SAMPLE table in LIMS to determine the lysis and elute plates associated with each quadrant
        The wells each plate is associate with is used to inffer the quadrant each plate went into (as there is
        no way of find the quadrant in LIMS any other way I'm aware of) and the resulting LYSIS and ELUTE IDs are saved
        to each plate

        Next it finds all the instruments assoicated with the 384-level POOL plate and sends that data to each plate object.

        Finally it sets each plate's thresholds based on which araya the plate was run on and the threshold values saved in
        the Pool Helper database. If a plate has no araya associated with it it's thresholds will be set to match the threshold
        of the first plate in this batch
        """
        if self.any_in_lims:
            lysis_elute_plates = app_func.lims_query(self._lysis_elute_plates_query())
            results = []
            plates = ()
            plates_with_pools = [x for x in self.plates if x.pool]

            for plate in plates_with_pools:
                result = plate.get_lysis_and_elute_plates([x[1:] for x in lysis_elute_plates if x[0] == plate.pool])
                results.append(result)
                result = (plate.pool, result['Q1'][0], result['Q1'][1], result['Q2'][0], result['Q2'][1], 
                            result['Q3'][0], result['Q3'][1], result['Q4'][0], result['Q4'][1])
                plates += tuple([x for x in result if not x == None])
            instruments = app_func.lims_query(self._instruments_query(plates))

            for idx, plate in enumerate(plates_with_pools):
                plate_plates = [x for x in results[idx] if len(x) > 12] + [results[idx]['Pool plate']] # List of sub-plates on the current plate
                plate.find_instruments([x for x in instruments if x[1] in plate_plates], results[idx])

                try:
                    plate.set_thresholds()
                except AttributeError:
                    araya = [x[0] for x in instruments if 'ARAYA' in [0]]
                    if araya:
                        plate.instruments['Araya'] = araya
                        LOGGER.warning(f'No araya found for plate {plate.array_code}, plate thresholds set based on the rest of the batch')
                    else:
                        plate.instruments['Araya'] = 'ARAYA_01'
                        LOGGER.warning(f'No araya found for plate {plate.array_code}, plate araya and thresholds defaulted to ARAYA_01')
                    plate.set_thresholds()

            self.thresholds = plates_with_pools[0].thresholds
            self.araya = plates_with_pools[0].araya
            plates_without_pools = [x for x in self.plates if not x.pool]

            for plate in plates_without_pools:
                plate.araya = self.araya
                plate.thresholds = self.thresholds
        else:
            self.plates[0].araya = self.araya
            self.plates[0].instruments = {'Araya': self.araya}
            self.plates[0].set_thresholds()
            self.thresholds = self.plates[0].thresholds
            
            for plate in self.plates[1:]:
                plate.araya = self.araya
                plate.thresholds = self.thresholds
                plate.instruments = self.plates[0].instruments

    def _comments_query(self):
        """
        Queries the C19_JOB_COMMENTS table in LIMS where JOB_HEADER is in a list of all plates (both 384 and 96) which are
        assoicated with all the plates in this batch. This is the currently set query:

        select COMMENTS, JOB_HEADER from C19_JOB_COMMENTS where JOB_HEADER in $all_plates

        RETURNS:
            pd.DataFrame - with a column containing each comment and a column containing the plate the comment reffers to
        """
        all_plates = []

        for plate in self.plates:
            if plate.pool:
                plate_plates = {
                    'Q1' : [plate.instruments['Q1'][1], plate.instruments['Q1'][0]],
                    'Q2' : [plate.instruments['Q2'][1], plate.instruments['Q2'][0]],
                    'Q3' : [plate.instruments['Q3'][1], plate.instruments['Q3'][0]],
                    'Q4' : [plate.instruments['Q4'][1], plate.instruments['Q4'][0]],
                    'Pool' : plate.instruments['Pool plate']
                    }
                all_plates.extend([x for x in list(plate_plates['Q1'] + plate_plates['Q2'] + plate_plates['Q3'] + plate_plates['Q4']) 
                                    if not x == ''])
                all_plates.append(plate_plates['Pool'])

        query = CONFIG['COMMENTS_QUERY']
        all_plates_str = str(tuple(all_plates))
        if len(all_plates) == 1:
            all_plates_str = all_plates_str.replace(',', '')
        query = query.replace('$all_plates', all_plates_str)

        return query

    def set_plate_comments(self):
        """For each plate which is in LIMS, sets it's comments by querying the LIMS mirror"""
        if self.any_in_lims:
            try:
                comments_df = pd.DataFrame(app_func.lims_query(self._comments_query()), columns = ('comment', 'plate'))
            except DatabaseError:
                self.comments = "ERROR - Could not fetch comments"
                comments_df = 'None'
            if not type(comments_df) == str:
                for plate in self.plates:
                    if plate.pool:
                        plate.get_comments(comments_df)
            else:
                for plate in self.plates:
                    plate.comments = 'Unavailable'

    def analyse_plates(self):
        """
        This iterates through each plate, using the plate's methods to analyse the plate (determining things such as it's 
        positivity rate and the CV of ROX ect...) and format it's data
        """
        for plate in self.plates:
            plate.data_as_df()
            plate.plate_analysis()
            plate.plate_info()
            plate.rox_box()
        
    def restamp_repool_vip_prio(self):
        """Determines if each plate (which is in LIMS) is a priority or VIP plate, or has been restamped / repooled"""
        if self.any_in_lims:
            pool_list = tuple([x.pool for x in self.plates if x.pool])
            if len(pool_list) == 1 and ',' in str(pool_list):
                pool_list = str(pool_list)[:-2] + ')'
            repool_restamp_query = CONFIG['REPOOL_RESTAMP_QUERY']
            repool_restamp_query = repool_restamp_query.replace('$plates$', str(pool_list))
            repooled_restamped = app_func.lims_query(repool_restamp_query)

            for plate in self.plates:
                if plate.pool:
                    repool_restamp_plate = [x for x in repooled_restamped if x[0] == plate.pool]
                    if repool_restamp_plate:
                        if repool_restamp_plate[0][1] == 'T':
                            plate.is_repooled = True
                        if repool_restamp_plate[0][2] == 'T':
                            plate.is_restamped = True
                if plate.check_if_vip():
                    plate.is_vip = True
                elif plate.check_if_prio():
                    plate.is_prio = True

    def create_html_stuff(self):
        for plate in self.plates:
            #plate.scatter_charts()
            plate.format_info()

    def _summary_buffer(self, df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic):
        """
        Appends the relevant data to the buffer summary (df). This function is for buffer plates
        
        PARAMETERS:
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
                
        RETERNS:
            The updated buffer summary dictionary, df
        """
        df['plate_type'].append('Possible Buffer')
        df['test_channel'].append('-')
        df['patient_samples'].append(0)
        df['positives'].append(len(plate_pos))
        df['plods'].append(len(plate_plods))
        df['vic_fails'].append('-')
        df['accu_fails'].append('-')
        df['negcon_fails'].append('-')
        df['poscon_fails'].append('-')
        df['pos_rate'].append('-')
        carry_overs = func.detect_carryover(plate_pos, plate_vic, plate_plods, previous_fam, previous_vic)
        df['pos_punch'].append(carry_overs[0])
        df['vic_punch'].append(carry_overs[1])
        df['plod_punch'].append(carry_overs[2])
        
        return df
    
    def _summary_patient(self, df, plate, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic, last_plate_buffer):
        """
        Appends the relevant data to the buffer summary (df). This function is for patient plates
        
        PARAMETERS:
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
                
        RETERNS:
            The updated buffer summary dictionary, df
        """
        df['plate_type'].append('Patient')
        channels = ''
        channels = app_func.find_test_channels_from_comments(plate)
        df['test_channel'].append(channels)
        #sample_wells = plate.df.loc[~plate.df['barcode'].isin(self.globals['NON_PATIENT_CODES'])]
        df['patient_samples'].append(plate.info['total_samples'][0])
        pos = len(plate.df.loc[(plate.df['nFAM'] >= self.thresholds['POSITIVE']) &
                               (plate.df['ROX'] >= self.thresholds['LOW_ROX']) &
                               ~(plate.df['barcode'].isin(self.plates[0].globals['NON_PATIENT_CODES']))])
        plods = len(plate.df.loc[(plate.df['nFAM'] >= self.thresholds['NEGATIVE']) &
                                (plate.df['nFAM'] < self.thresholds['POSITIVE']) &
                               (plate.df['ROX'] >= self.thresholds['LOW_ROX']) &
                               ~(plate.df['barcode'].isin(self.plates[0].globals['NON_PATIENT_CODES']))])
        df['positives'].append(pos)
        df['plods'].append(plods)
        df['vic_fails'].append(plate.info['vic_fails'][0])
        controls_df = plate.df.loc[plate.df['barcode'] == 'Con']
        df['accu_fails'].append(len(controls_df.loc[(((controls_df['nFAM'] < self.thresholds['POSITIVE']) |
                                                (controls_df['nVIC'] >= self.thresholds['nVIC'])) &
                                                (controls_df['well'].isin(self.plates[0].globals['ACCUPLEX_WELLS'])) &
                                                (controls_df['ROX'] >= self.thresholds['LOW_ROX'])) |
                                                ((controls_df['ROX'] < self.thresholds['LOW_ROX']) &
                                                (controls_df['well'].isin(self.plates[0].globals['ACCUPLEX_WELLS'])))]))
        df['poscon_fails'].append(len(controls_df.loc[((controls_df['nFAM'] < self.thresholds['POSITIVE']) &
                                                 (controls_df['barcode'] == 'Con') &
                                                 (controls_df['well'].isin(self.plates[0].globals['QNOS_WELLS'])) &
                                                 (controls_df['ROX'] >= self.thresholds['LOW_ROX'])) |
                                                 ((controls_df['ROX'] < self.thresholds['LOW_ROX']) &
                                                (controls_df['well'].isin(self.plates[0].globals['QNOS_WELLS'])))]))
        df['negcon_fails'].append(len(controls_df.loc[((controls_df['nFAM'] >= self.thresholds['NEGATIVE']) &
                                                 (controls_df['barcode'] == 'Con') &
                                                 (controls_df['well'].isin(self.plates[0].globals['NEGCON_WELLS']) &
                                                 (controls_df['ROX'] >= self.thresholds['LOW_ROX']))) |
                                                 ((controls_df['ROX'] < self.thresholds['LOW_ROX']) &
                                                (controls_df['well'].isin(self.plates[0].globals['NEGCON_WELLS'])))]))
        if df['patient_samples'][-1] > 0:
            df['pos_rate'].append(str(app_func.round_fixed((plate.info['positives'][0] / plate.info['total_samples'][0]) * 100, 2)) + '%')
        else:
            df['pos_rate'].append('0')
        if last_plate_buffer:
            carry_overs = func.detect_carryover(plate_pos, plate_vic, plate_plods, previous_fam, previous_vic)
        else:
            carry_overs = ('-', '-', '-')
        df['pos_punch'].append(carry_overs[0])
        df['vic_punch'].append(carry_overs[1])
        df['plod_punch'].append(carry_overs[2])
        
        return df        
          
    def buffer_summary(self):
        """
        Builds a buffer summary for the batch of plates being analysed
        
        RETERNS:
            A pd.DataFrame in the form of a buffer summary table containing the data for this plate batch's buffer summary

        To add:
            Contams
            Contam wells?
            VIC contams?
        """

        #
        df = dict(plates = self.array_codes,
            plate_type = [],
            read_date = [],
            test_channel = [],
            patient_samples = [],
            positives = [],
            plods = [],
            vic_fails = [],
            rox_failures = [],
            accu_fails = [],
            negcon_fails = [],
            poscon_fails = [],
            pos_rate = [],
            pos_punch = [],
            plod_punch = [],
            vic_punch = []
            )
        
        # These will be used to keep track of the positions of positives on previous plates:
        previous_fam = []
        previous_vic = []
        last_plate_buffer = False
        
        for plate in self.plates:
            plate_pos = plate.df.loc[plate.df['nFAM'] >= self.thresholds['POSITIVE']]['well']
            plate_plods = plate.df.loc[(plate.df['nFAM'] >= self.thresholds['NEGATIVE']) & 
                                      ( plate.df['nFAM'] < self.thresholds['POSITIVE'])]['well']
            pos_vic = plate.df.loc[plate.df['nVIC'] >= self.thresholds['nVIC']]['well']
            df['rox_failures'].append(len(plate.df.loc[plate.df['ROX'] < plate.thresholds['LOW_ROX']]))
            
            if plate.pool == None:
                df = self._summary_buffer(df, plate_pos, pos_vic, plate_plods, previous_fam, previous_vic)
                last_plate_buffer = True
                
            else:
                df = self._summary_patient(df, plate, plate_pos, pos_vic, plate_plods, previous_fam, previous_vic, last_plate_buffer)
                last_plate_buffer = False
                
            df['read_date'].append(plate.read_date[0:10].replace(':', '/') + ' ' + plate.read_date[11:16])
            previous_fam = list(plate_pos)
            previous_vic = list(pos_vic)
        df = pd.DataFrame(df)
        df.rename({
            'plates' : 'Plate', 'plate_type' : 'Type', 'read_date' : 'Read Date', 'test_channel' : 'Channel',
            'patient_samples' : 'Num Samples', 'positives' : 'Positives', 'plods' : 'PLODs', 'vic_fails' : 'VIC Fails',
            'rox_failures' : 'Low ROX', 'accu_fails' : 'Accuplex Fails', 'negcon_fails' : 'Negcon Fails', 
            'poscon_fails' : 'Qnos Fails', 'pos_rate' : 'Patient Positivity', 'pos_punch' : 'Pos Punch', 
            'plod_punch' : 'Pos to PLOD', 'vic_punch' : 'VIC Punch'
            }, axis = 1, inplace = True)
        LOGGER.info('Buffer summary complete')
        self.summary = pd.DataFrame(df)

    def create_unique_batchname(self):
        """
        Creates a unique batchname for this batch with the format: 'lowest_array_code - highest_array_code'
        If a batch with that name already exists in the database it will append an appropriate number to the end of the name
        """
        self.unique_batchname = self.plates[0].array_code + ' - ' + self.plates[-1].array_code
        count = Batch.objects.filter(batch__startswith = self.unique_batchname).count()
        if count:
            self.unique_batchname += ' ' + str(count)

    def create_unique_platenames(self):
        """
        For each plate reates a unique platename for this batch with the format: 'plate_array_code'
        If a plate with that name already exists in the database it will append an appropriate number to the end of the name

        RETURNS:
            str - A list of each plate's unique platename for the Pool Helper database
        """
        plate_names = ''
        for plate in self.plates:
            plate.set_unique_platename()
            plate_names += '-' + plate.unique_platename
        
        return plate_names[1:]
    
    def save_plates_to_db(self, batch, user = None):
        """Saves each plate and all it's samples to the Pool Helper database using the plate's save method"""
        for plate in self.plates:
            plate.save_to_db(batch, user)

    def save_batch_to_db(self, plate_names, user = None):
        """Saves the batch and each plate and each plate's samples to the Pool Helper database"""
        analysed_batch = Batch(
            batch = self.unique_batchname,
            plates = plate_names,
            batch_time = datetime.now(),
            araya = self.araya,
            escalations = str([x.unique_platename for x in self.plates if x.escalated]).replace(']', '').replace('[', '').replace("'", ""),
            summary = self.summary.to_html(index=False),
            buffers = str([x.unique_platename for x in self.plates if not x.pool]).replace(']', '').replace('[', '').replace("'", ""),
            prio_plates = str([x.unique_platename for x in self.plates if x.is_prio]).replace(']', '').replace('[', '').replace("'", ""),
            plates_to_do = str([x.unique_platename for x in self.plates if x.pool]).replace(']', '').replace('[', '').replace("'", "")
        )
        if user:
            analysed_batch.uploaded_by = user
        analysed_batch.save()

        self.save_plates_to_db(analysed_batch, user)
