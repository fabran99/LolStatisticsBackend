from __future__ import absolute_import, unicode_literals
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from redis import Redis
import os
from datetime import datetime as dt, timedelta as td
from stats import stats_functions
from lol_stats_api.helpers.variables import player_sample
from stats import get_players
from stats import get_matches
from lol_stats_api.helpers.mongodb import get_mongo_players, get_mongo_stats

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))
db_players = get_mongo_players()
db_stats = get_mongo_stats()


@periodic_task(name="update_player_list",
    run_every=(crontab(day_of_week='1,3,5',hour="3" ,minute='5'))
)
def periodically_update_player_list():
    """
    Actualiza periodicamente la lista de jugadores
    """
    get_players.update_player_list()

@periodic_task(name="clear_old_data",
    run_every=(crontab(hour="*/3" ,minute='35'))
)
def clear_data_from_3_days_ago():
    """
    Elimina los datos de hace mas de 3 dias
    """
    timestamp = get_matches.x_days_ago(3)
    print("Eliminando datos anteriores a {}".format(timestamp))
    # Timelines
    print("Eliminando timelines")
    db_stats.timelines.remove({'gameTimestamp':{"$lt":timestamp}})
    # Bans
    print("Eliminando bans")
    db_stats.bans.remove({'timestamp':{"$lt":timestamp}})
    # Champ data
    print("Eliminando champ data")
    db_stats.champ_data.remove({'timestamp':{"$lt":timestamp}})
    # Playstyle
    print("Eliminando champ playstyle")
    db_stats.champ_playstyle.remove({'timestamp':{"$lt":timestamp}})



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
    