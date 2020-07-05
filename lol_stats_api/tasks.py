from __future__ import absolute_import, unicode_literals
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from redis import Redis
import os
from datetime import datetime as dt, timedelta
from stats import stats_functions
from lol_stats_api.helpers.variables import player_sample
from stats import get_players
from stats import get_matches

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))


@periodic_task(name="update_player_list",
    run_every=(crontab(day_of_week='1,4',hour="3" ,minute='5'))
)
def periodically_update_player_list():
    """
    Actualiza periodicamente la lista de jugadores
    """
    get_players.update_player_list()


@task(name="update_players")
def update_player_detail_in_celery(current_player):
    """
    Actualiza la informacion de un jugador
    """
    get_players.update_player_detail(current_player)


@task(name="process_match")
def process_match_with_celery(match):
    """
    Procesa una partida con celery
    """
    get_matches.process_match(match)
    