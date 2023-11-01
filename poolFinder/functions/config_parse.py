from django.db.utils import OperationalError
from poolFinder.models import PoolFinderConfig
import cx_Oracle


def lims_login(username, password):
    connection = cx_Oracle.connect(user=username,password=password,dsn="LIMSREP")
    connection.current_schema = 'VGSM'
    return connection


def config_parse():
    try:
        config_dictionary = {}
        configs = PoolFinderConfig.objects.all()
        for option in configs:
            config_dictionary[option.option] = option.value

        if 'MIRROR_USERNAME' in config_dictionary and 'MIRROR_PASSWORD' in config_dictionary:
            config_dictionary['CONNECTION'] = lims_login(config_dictionary['MIRROR_USERNAME'], config_dictionary['MIRROR_PASSWORD'])
            config_dictionary['CUR'] = config_dictionary['CONNECTION'].cursor()
        return config_dictionary

    except OperationalError:
        return

CONFIG = config_parse()
