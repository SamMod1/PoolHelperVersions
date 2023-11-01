from django.apps import AppConfig
import os


class PoolfinderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'poolFinder'

    def ready(self):
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE') 
        if run_once is not None:
            return
        os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True' 
        from BackgroundTasks.jobs import start_tasks
        start_tasks() # Use Celery
        