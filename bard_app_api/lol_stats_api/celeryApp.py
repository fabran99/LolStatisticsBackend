# from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import django
from celery.schedules import crontab
from lol_stats_api.helpers.variables import cron_players

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lol_stats_api.settings")
# django.setup()
app = Celery('lol_stats_api')
app.conf.broker_transport_options = {'visibility_timeout': 36000}

app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()

app.conf["result_backend_transport_options"] = {'visibility_timeout': 18000}


app.conf.beat_schedule = {
    'update_player_list_periodically':{
        'task':'periodically_update_player_list',
        'schedule':crontab(**cron_players),
    },
    'clear_old_data':{
        'task':'clear_old_data',
        'schedule':crontab(hour="*/3", minute='35')
    },
    'clear_redis_old_data':{
        'task':'clear_redis_old_data',
        'schedule':crontab(minute='*/20')
    },
    'periodically_generate_new_stats':{
        'task':'periodically_generate_new_stats',
        'schedule':crontab(minute='30', hour="5",day_of_week="1")
    },
    'periodically_update_assets':{
        'task':'periodically_update_assets',
        'schedule':crontab(minute='20', hour="*/4")
    }
}