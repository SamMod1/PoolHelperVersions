import logging
import requests
from time import sleep
from multiprocessing import Process
from requests.exceptions import ConnectionError


SERVER_PORT = '8000'
LOGGER = logging.getLogger('django')


class Scheduler:
    def __init__(self, func, interval: int, args = None):
        """
        A simple timer class which will schedule a task (func : callable) to run every x (interval) seconds

        Parameters:
            func : callable or list of callables
                Some function(s) to be called each time interval
            interval : number
                The time (in seconds) for which to wait between each call of func
            args : dict or list of dicts = None
                The arguments as a list of dictionaries to pass to each callable in func. The order of each dictionary
                of arguments must match the order of the callables to which these arguments should be passed
        """
        self.func = func
        self.args = args
        self.interval = interval
        self.running = False
    
    def loop(self):
        """The function which calls self.func"""
        print('Starting background tasks...')
        try:
            sleep(5)
            requests.get('http://localhost:' + SERVER_PORT)
        except ConnectionError:
            LOGGER.info("Background Processes not started because the server isn't running")
            return
        from django import setup
        global DJANGO_SETTINGS_MODULE
        import rfl.settings as DJANGO_SETTINGS_MODULE
        log_name = DJANGO_SETTINGS_MODULE.LOGGING['handlers']['file']['filename'].rsplit('.', 1)
        log_name = log_name[0] + '_background_process.' + log_name[1]
        DJANGO_SETTINGS_MODULE.LOGGING['handlers']['file']['filename'] = log_name
        setup()
        from importlib import import_module
        self.running = True
        if type(self.func) == list:
            func_list = []
            for idx in range(self.func):
                func = self.func[idx].rsplit('.', 1)
                func_list.append(getattr(func[0], func[1]))
            while self.running:
                sleep(self.interval)
                for idx, func in enumerate(func_list):
                    if self.args[idx]:
                        func(**self.args[idx])
                    else:
                        func()
        else:
            self.func = self.func.rsplit('.', 1)
            real_func = getattr(import_module(self.func[0]), self.func[1])
            while self.running:
                sleep(self.interval)
                if self.args:
                    real_func(**self.args)
                else:
                    real_func()

    def start(self):
        self.running = True
        process = Process(target = self.loop)
        process.start()
        process_name = process.pid
        return process_name
    
    def stop(self):
        self.running = False
