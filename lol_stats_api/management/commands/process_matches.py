from django.core.management.base import BaseCommand, CommandError
from redis import Redis
from datetime import timedelta as dt, datetime as td
import os
from time import sleep
from lol_stats_api import tasks
import json
from stats.get_matches import x_days_ago


db_matchlist = Redis(db=os.getenv("REDIS_GAMELIST_DB"), decode_responses=True)
db_celery = Redis(db=os.getenv("CELERY_DB"), decode_responses=True)

def process_match_for_each_key():
    """
    Envia a la cola de celery para procesar una de cada server que este corriendo
    """
    number = 1 if len(db_matchlist.keys()) > 5 else 5
    for server in db_matchlist.keys():
        for i in range(number):
            match = db_matchlist.lpop(server)
            if match is None:
                break
            data_match = json.loads(match)
            timestamp = x_days_ago(3)

            if match and data_match['timestamp']> timestamp:
                print(data_match)
                tasks.process_match_with_celery.delay(match)


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            # Evito saturar la cola de redis, solo envio partidas si 
            # la cola tiene 50 o menos elementos
            els = db_celery.llen('celery') 
            if els > 50:
                print("Esperando a que la cola se vacie - {} elementos".format(els))
                sleep(10)
                continue
            else:
                process_match_for_each_key()
                sleep(0.5)
