from django.core.management.base import BaseCommand, CommandError
from redis import Redis
import os
from time import sleep
from lol_stats_api import tasks
import json

db_matchlist = Redis(db=os.getenv("REDIS_GAMELIST_DB"), decode_responses=True)

def process_match_for_each_key():
    """
    Envia a la cola de celery para procesar una de cada server que este corriendo
    """
    for server in db_matchlist.keys():
        match = db_matchlist.rpop(server)
        print("Procesando partida {}".format(str(json.loads(match)['gameId'])))
        if match:
            tasks.process_match_with_celery.delay(match)


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            process_match_for_each_key()
            sleep(1.5)
