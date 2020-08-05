from __future__ import absolute_import, unicode_literals
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from redis import Redis
from celery_singleton import Singleton,clear_locks
import os
from datetime import datetime as dt, timedelta as td
from lol_stats_api.helpers.variables import player_sample, cron_players
from stats import get_players,get_matches,calculations
from assets.load_data import load_data
from lol_stats_api.helpers.mongodb import get_mongo_players, get_mongo_stats
from celery.signals import worker_ready

from assets.ddragon_routes import get_current_version
from lol_stats_api.helpers.mongodb import get_saved_version


from lol_stats_api.celery import app
import json

@worker_ready.connect
def unlock_all(**kwargs):
    print("Test")
    clear_locks(app)

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))
db_matchlist = Redis(db=os.getenv("REDIS_GAMELIST_DB"), decode_responses=True)
db_players = get_mongo_players()
db_stats = get_mongo_stats()


# Jugadores
@periodic_task(name="update_player_list_periodically",
    run_every=(crontab(**cron_players))
)
def periodically_update_player_list():
    """
    Actualiza periodicamente la lista de jugadores
    """
    update_player_list.delay()
    

@app.task(base=Singleton,name="update_player_list")
def update_player_list():
    print("Inicio el updateo de jugadores")
    get_players.update_player_list()

@task(base=Singleton,name="update_players")
def update_player_detail_in_celery(current_player):
    """
    Actualiza la informacion de un jugador
    """
    get_players.update_player_detail(current_player)



# Limpieza periodica
@periodic_task(name="run_clear_old_data",
    run_every=(crontab(hour="*/3" ,minute='35'))
)
def run_clear_data():
    clear_data_from_3_days_ago.delay()


@task(base=Singleton,name="clear_old_data")
def clear_data_from_3_days_ago():
    """
    Elimina los datos de hace mas de 3 dias
    """
    timestamp = get_matches.x_days_ago(3)
    more_time_ago = get_matches.x_days_ago(5)
    print("Eliminando datos anteriores a {}".format(timestamp))
    # Timelines
    print("Eliminando timelines")
    db_stats.timelines.remove({'gameTimestamp':{"$lt":more_time_ago}})
    print("Eliminando skill_ups")
    db_stats.skill_up.remove({'timestamp':{"$lt":more_time_ago}})
    # Bans
    print("Eliminando bans")
    db_stats.bans.remove({'timestamp':{"$lt":timestamp}})
    # Champ data
    print("Eliminando champ data")
    db_stats.champ_data.remove({'timestamp':{"$lt":timestamp}})
    # Playstyle
    print("Eliminando champ playstyle")
    db_stats.champ_playstyle.remove({'timestamp':{"$lt":timestamp}})


@periodic_task(name="clear_redis_old_data",
    run_every=(crontab(minute='*/20'))
)
def clear_redis_from_3_days_ago():
    """
    Reviso key por key si la ultima es muy vieja, y mientras lo sea sigo eliminando
    """
    for server in db_matchlist.keys():
        print("Revisando server - {}".format(server))
        while True:
            # Tomo la ultima del actual
            match = db_matchlist.rpop(server)
            if match is None:
                break
            
            data_match = json.loads(match)
            timestamp = get_matches.x_days_ago(3)
            # Si esta dentro del rango, la vuelvo a colocar y continuo
            if data_match['timestamp'] > timestamp:
                db_matchlist.rpush(server,match)
                break
            print("Elimino match: {}".format(match))



# Matches
@task(base=Singleton,name="process_match")
def process_match_with_celery(match):
    """
    Procesa una partida con celery
    """
    get_matches.process_match(match)
    


# Estadisticas
@periodic_task(name="periodically_generate_new_stats",
    run_every=(crontab(minute='45', hour="20,8"))
)
def periodically_generate_new_stats():
    """
    Ejecuta periodicamente el calculo de estadisticas
    """
    generate_new_stats.delay()

@task(base=Singleton,name="generate_stats")
def generate_new_stats():
    """
    Genera las estadisticas
    """
    calculations.generate_builds_stats_by_champ()



# Assets
@periodic_task(name="periodically_update_assets",
    run_every=(crontab(minute='20', hour="*/6"))
)
def periodically_update_assets():
    """
    Ejecuta periodicamente el update de assets
    """
    update_assets.delay()


@task(base=Singleton,name="update_assets")
def update_assets():
    """
    Actualiza los assets
    """
    saved_version = get_saved_version()
    game_version = get_current_version()
    # Si la version es distinta actualizo
    if saved_version != game_version:
        load_data()
        # Recalculo las estadisticas
        generate_new_stats.delay()