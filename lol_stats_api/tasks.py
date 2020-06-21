from __future__ import absolute_import, unicode_literals
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from redis import Redis
import os
from datetime import datetime as dt, timedelta
from stats import stats_functions
from lol_stats_api.helpers.variables import player_sample

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))


@periodic_task(name="check_last_update",
    run_every=(crontab(hour='20,1,8,13', minute='5'))
)
def check_last_update():
    """
    Checkea la ultima hora de actualizacion, si pasaron mas de 6 horas, entonces
    mando a actualizar
    """
    last_update_date = db_metadata.get("last_update_date")

    if not last_update_date:
        print("not last update")
        db_metadata.set("running","0")
        update_stats_with_celery.delay()
        return
    current_time = int(dt.now().timestamp())
    td = timedelta(hours=15).total_seconds()
    if current_time - int(last_update_date) >= td:
        print(current_time - int(last_update_date))
        db_metadata.set("running","0")
        update_stats_with_celery.delay()


@periodic_task(name="automatically_update_stats",
    run_every=(crontab(hour='20,0,5,10,15', minute='0'))
)
def automatically_update_stats():
    """
    Manda a actualizar las stats cada 5 horas
    """
    update_stats_with_celery.delay()


@task(name="update_stats")
def update_stats_with_celery():
    """
    Manda a actualizar las stats
    """
    try:
        stats_functions.process_stats()
    except Exception as e:
        print(e)
        db_metadata.set("running","0")
