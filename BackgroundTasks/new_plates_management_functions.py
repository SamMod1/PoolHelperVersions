import io
import logging
import numpy as np
from django.contrib.auth.models import User
from poolFinder.models import AnalysedPlate, Batch
from poolFinder.functions.config_parse import CONFIG
import poolFinder.functions.app_functions as func
from unittest.mock import patch
from BackgroundTasks.PlateAnalysis.classes.analysis_functions import add_leading_zeros
from poolFinder.unit_test_resources.helper_functions_and_classes import CallableGenerator


global_callable_generator = CallableGenerator()
logger = logging.getLogger('django')


def update_previous_plates_and_batches(plates_in_fastfinder):
    """
    Takes a list of plates currently sent to FastFinder by LIMS. Any plates and batches in Pool Helper with the status
    in_ff = True which are not in this list will be altered so that in_ff = False (and a bit more goes on)
    """
    in_ff = plates_in_fastfinder
    
    for plate in AnalysedPlate.objects.filter(in_ff = True).all():
        db_plate = plate.array_code[:6]
        if not db_plate in in_ff:
            plate.in_ff = False
            plate.save()
            logger.info('Updated plate ' + db_plate)

    for batch_in_ff in Batch.objects.filter(in_ff=True):
        plates = AnalysedPlate.objects.filter(array_code__in=batch_in_ff.plates.split('-')).all()
        plates_in_ff = ''
        hidden = True
        for plate in plates:
            if plate.array_code in in_ff:
                if hidden:
                    if plate.show_in_plates_in_fastfinder:
                        hidden = False
                plates_in_ff += ', ' + plate.array_code
        if hidden or not plates_in_ff:
            batch_in_ff.plates_to_do = ''
            batch_in_ff.in_ff = False
            batch_in_ff.save()
            logger.info('Updated batch ' + batch_in_ff.batch)
        else:
            batch_in_ff.plates_to_do = plates_in_ff[2:]
            batch_in_ff.save()


def decode_file(file):
    """
    Takes an araya file as a bytes file and decodes it into a normal string
    """
    b_file = io.BytesIO(file.read()).readlines()
    file = []
    for b_line in b_file:
        line = b_line.decode()
        file.append(line)
    return file


def array_pools_from_array_code(array_code, user):
    """
    PARAMETERS:
        array_code: str - The array code of one array in the batch
        cur - cx_Oracle cursor object connecting to the LIMS mirror
        user - The user uploading the batch

    RETURNS:
        list - contains one tuple with the plate's array code and the plate's pool ID (if it has one)
    """
    logger.info(f'Analysis of batch containing {array_code} manually requested by {user}')
    query = CONFIG['POOL_QUERY'].split('$or$')[1].replace('$array_code$', array_code)
    array_pools = func.lims_query(query)

    if not array_pools:
            array_pools = [(array_code, None)]
    
    return array_pools


def array_pools_from_files(files, user):
    """
    Using a list of araya files and their array codes, this function queries the LIMS mirror to check whether any
    of the uploaded plates have pool plates associated with them. It then returns this data.

    PARAMETERS:
        files - a list of file objects (from request.FILES.getlist('upload')). These file objects must have two attributes:
            name: must be the name of the array code. E.g. '20220906085838_00890018002017-00620201218-673678.csv'
            file: A binary file object which can be decoded by io.BytesIO

    RETURNS:
        list - contains tuples for each file containing the array code and the pool ID (if it has one)
        dict - contains the files, matched to the array code for that file as the key
    """
    file_dict = {}

    for file in files:
        array_code = file.name[-10:-4]
        logger.info(array_code + ' manually uploaded by ' + user)
        file_dict[array_code] = decode_file(file.file)
        if len(file_dict) == 1:
            array_codes = str(tuple(file_dict.keys())).replace(',', '')
        else:
            array_codes = str(tuple(file_dict.keys()))

    query = CONFIG['POOL_QUERY'].split('$or$')[0].replace('$array_codes$', array_codes)
    array_pools = func.lims_query(query)
    
    return array_pools, file_dict


def analyse_and_save_batch(batch, user = None):
    """
    By calling the various class methods in the given batch, this function analyses the batch, then saves the analysed
    batch to the Pool Helper database

    RETURNS:
        str - the unique batchname in the format 'lowest_array_code - highest_array_code' of the saved batch 
              (if a batch already exists with this name it will append a number to the end to make it unique)
    """
    if user:
        user = User.objects.filter(username=user).first()

    batch.set_plate_data()

    batch.set_plate_instruments()

    batch.set_plate_comments()

    batch.analyse_plates()

    batch.create_html_stuff()

    batch.restamp_repool_vip_prio()

    batch.buffer_summary()

    batch.create_unique_batchname()
    
    plate_names = batch.create_unique_platenames()

    duped_plates = [x for x in plate_names.split('-') if ' ' in x]
    if duped_plates:
        for plate in duped_plates:
            for plate_in_batch in batch.plates:
                if plate[:6] == plate_in_batch.array_code:
                    plate_in_batch.array_code = plate
                    break

    batch.save_batch_to_db(plate_names, user = user)

    return batch.unique_batchname


def setup_test_batch(array_pools, files):
    if not array_pools:
        array_pools = []
        for idx, file in enumerate(files):
            array_pools.append((file, 'POOL' + add_leading_zeros(str(idx), 8)))
    
    return array_pools, files


@patch("poolFinder.functions.app_functions.lims_query", global_callable_generator)
def analyse_and_save_batch_test(batch, user = None):
    """
    Test version of the above function

    RETURNS:
        str - the unique batchname in the format 'lowest_array_code - highest_array_code' of the saved batch 
              (if a batch already exists with this name it will append a number to the end to make it unique)
    """
    global global_callable_generator
    if user:
        user = User.objects.filter(username=user).first()

    pools = [x.pool for x in batch.plates if x.pool]
    barcodes = []
    for pool in pools:
        barcodes.append((pool, 'AAA', 'A01'))
    global_callable_generator.set_new_generator([barcodes])
    batch.set_plate_data()

    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    for plate in batch.plates:
        plate.barcodes_from_matrix(barcodes)

    plates = []
    instruments = []
    for idx, pool in enumerate(pools):
        plates.extend([(pool, f'INACT000000{str(idx)}1', f'ELUTE000000{str(idx)}1', 'A01'), 
        (pool, f'INACT000000{str(idx)}2', f'ELUTE000000{str(idx)}2', 'A02'), (pool, f'INACT000000{str(idx)}3', 
        f'ELUTE000000{str(idx)}3', 'B01'), (pool, f'INACT000000{str(idx)}1', f'ELUTE000000{str(idx)}1', 'A01')])
        instruments.extend([
        ('HAM_DWP_01', f'INACT000000{str(idx)}1'), ('KF_01', f'ELUTE000000{str(idx)}1'), (batch.araya, pool), 
        ('DRAGONFLY_02', f'ELUTE000000{str(idx)}2'), ('DRAGONFLY_01', f'ELUTE000000{str(idx)}1'), 
        ('HAM_DWP_02', f'INACT000000{str(idx)}2'), ('KF_02', f'ELUTE000000{str(idx)}2'),
        ('HAM_DWP_03', f'INACT000000{str(idx)}3'), ('KF_03', f'ELUTE000000{str(idx)}3'), ('DRAGONFLY_03', f'ELUTE000000{str(idx)}3'),
        ('NEXAR_01', pool), ('HYDROCYCL_01', pool), ('HAM_384_01', pool)
        ])
    global_callable_generator.set_new_generator([plates, instruments])
    batch.set_plate_instruments()

    comments = []
    for idx, pool in enumerate(pools):
        comments.extend([
            ('Pool plate comment', pool), (f'Elute {str(idx)}1 comment', f'ELUTE000000{str(idx)}1'), 
            (f'Inact {str(idx)}1 comment', f'INACT000000{str(idx)}1'), (f'Elute {str(idx)}2 comment', f'ELUTE000000{str(idx)}2'), 
            (f'Inact {str(idx)}2 comment', f'INACT000000{str(idx)}2'), (f'Elute {str(idx)}3 comment', f'ELUTE000000{str(idx)}3'), 
            (f'Inact {str(idx)}3 comment', f'INACT000000{str(idx)}3'), (f'Elute {str(idx)}1 comment 2', f'ELUTE000000{str(idx)}1')
        ])
    global_callable_generator.set_new_generator([comments])
    batch.set_plate_comments()

    batch.analyse_plates()

    batch.create_html_stuff()

    global_callable_generator.set_new_generator([[('POOL00000001', 'F', 'F')]])
    batch.restamp_repool_vip_prio()

    batch.buffer_summary()

    batch.create_unique_batchname()
    
    plate_names = batch.create_unique_platenames()

    duped_plates = [x for x in plate_names.split('-') if ' ' in x]
    if duped_plates:
        for plate in duped_plates:
            for plate_in_batch in batch.plates:
                if plate[:6] == plate_in_batch.array_code:
                    plate_in_batch.array_code = plate
                    break

    batch.save_batch_to_db(plate_names, user = user)

    return batch.unique_batchname
