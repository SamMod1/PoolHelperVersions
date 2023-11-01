from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from kombu import Queue, Exchange

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rfl.settings')

app = Celery('rfl', task_cls='lib.transaction_aware_celery_task.TransactionAwareCeleryTask')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# app.conf.broker_transport_options = {
#     'queue_order_strategy': 'priority',
# }

app.conf.task_create_missing_queues = True

app.conf.worker_prefetch_multiplier = 1
app.conf.task_inherit_parent_priority = True
