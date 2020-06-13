from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import django
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lol_stats_api.settings")
django.setup()
app = Celery('lol_stats_api')
app.conf.broker_transport_options = {'visibility_timeout': 36000}

app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()
