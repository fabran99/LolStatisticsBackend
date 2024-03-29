from django.core.management.base import BaseCommand, CommandError
from redis import Redis
from datetime import timedelta as dt, datetime as td
import os
from time import sleep
from lol_stats_api import tasks
import json
from lol_stats_api.helpers.variables import cron_players_text
from stats.get_matches import x_days_ago
from datetime import datetime as dt, timedelta as td
import croniter
from lol_stats_api.helpers.redis import db_matchlist, db_celery


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

            if match and data_match['timestamp'] > timestamp:
                tasks.process_match_with_celery.delay(match)


def check_player_update_running():
    """
    Retorna si falta poco, o estoy actualizando a los jugadores
    """
    now = dt.utcnow()
    cron = croniter.croniter(cron_players_text, now)
    next_exec = dt.fromtimestamp(cron.get_next())
    prev_exec = dt.fromtimestamp(cron.get_prev())

    offset_prev = td(minutes=10)
    offset_next = td(hours=2)

    if next_exec <= now + offset_prev:
        # Si faltan menos de 10 minutos para correr el script dejo de procesar
        return True

    return False


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            # Reviso que no este pidiendo datos de jugadores
            if check_player_update_running():
                sleep(60*60)
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
