import logging
from multiprocessing.dummy import Pool
from poolFinder.functions.app_functions import lims_query
from .classes.batch_analysis import BatchAnalysis
from poolFinder.models import AnalysedPlate
from poolFinder.functions.config_parse import CONFIG
import BackgroundTasks.PlateAnalysis.new_plates_management_functions as func


logger = logging.getLogger('django')


def check_for_plates():
    """
    This function starts by querying the LIMS mirror for any plates which have been sent to FastFinder, but which
    haven't been released from FastFinder yet

    It then updates any plates and batches in Pool Helper which were in FastFinder but are not any longer

    Finally it creates any new batches which have just come into FastFinder which aren't already contained in the
    Pool Helper database
    """
    logger.info('Checking for new plates...')

    if CONFIG['TEST_MODE'] == 'TRUE':
        logger.warning('Check cancelled because program is in test mode')
        return

    query = CONFIG['PLATES_IN_FF_QUERY']
    query_response = lims_query(query)

    array_codes_of_plates_in_ff = [x[0] for x in query_response]
    func.update_previous_plates_and_batches(array_codes_of_plates_in_ff)

    new_plates = []
    for plate in query_response:
        if not AnalysedPlate.objects.filter(array_code=plate[0]).exists():
            new_plates.append(plate)

    if not new_plates:
        return
    batch = BatchAnalysis(new_plates)

    logger.info('New plates found:')
    for plate in batch.plates:
        logger.info(plate.array_code)

    func.analyse_and_save_batch(batch)


def manual_upload(files_or_array, user: str, araya):
    """
    This takes either a list of files or simply an array code. It then creates and analyses a new batch based on this,
    saving it to the Pool Helper database
    """

    if type(files_or_array) == str:
        array_pools = func.array_pools_from_array_code(files_or_array, user)
        file_dict = {}
    else:
        array_pools, file_dict = func.array_pools_from_files(files_or_array, user)

    if CONFIG['TEST_MODE'] == 'TRUE':
        array_pools, file_dict = func.setup_test_batch(array_pools, file_dict)
        batch = BatchAnalysis(array_pools, files = file_dict, araya = araya)
        batch_name = func.analyse_and_save_batch_test(batch, user)
    else:
        batch = BatchAnalysis(array_pools, files = file_dict, araya = araya)
        batch_name = func.analyse_and_save_batch(batch, user)
    
    return batch_name
