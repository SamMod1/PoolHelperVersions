from .scheduler import Scheduler
#from BackgroundTasks.PlateAnalysis.new_plates_manager import check_for_plates
from poolFinder.functions.config_parse import CONFIG
import logging


logger = logging.getLogger('django')


def start_tasks():
    """
    Uses the Scheduler class to set and run various tasks on different threads at various intervals of time
    
    Tasks which will be started by this function:
        check_for_plates (every 20s) - Runs LIMS queries to check for new plates to add to the Pool Helper database, adds
            plates where necissary

    NOTE:
        The lines involving the started variable and running.txt are there for development purposes. Unless removed they will
        break this function if django's dev-mode is turned off on the server

    RETURNS:
        The process ID for the process that gets started
    """
    if 'MIRROR_PASSWORD' in CONFIG and 'MIRROR_USERNAME' in CONFIG:
        logger.info('Starting scheduled tasks...')
        scheduler = Scheduler(
            'BackgroundTasks.PlateAnalysis.new_plates_manager.check_for_plates', 
            int(CONFIG['REFRESH_RATE'])
        )
        scheduler.start()
            