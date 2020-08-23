import pymongo
from django.conf import settings
from monary import Monary
from redis import Redis
import os
db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"), decode_responses=True)


def get_mongo():
    """
    Devuelve conexion con mongodb
    """
    client = pymongo.MongoClient(
        host=settings.MONGO_DB_HOST,
        port=27017
    )
    return client


def get_mongo_assets():
    """
    Devuelve conexion con mongodb de assets
    """
    client = get_mongo()
    mongodb = client.assets
    return mongodb


def get_mongo_players():
    """
    Devuelve conexion con mongodb de jugadores
    """
    client = get_mongo()
    mongodb = client.players
    return mongodb


def get_monary():
    """
    Devuelve conexion de monary
    """
    client = Monary(settings.MONGO_DB_HOST, 27017)
    return client


def get_mongo_stats():
    """
    Devuelve conexion con mongodb de datos
    """
    client = get_mongo()
    mongodb = client.statistics
    return mongodb


def get_saved_version():
    """
    Devuelve la ultima version cuyos datos han sido actualizados
    en mongo
    """
    current_version = db_metadata.get("current_version")
    return current_version

def get_last_calculated_patch():
    """
    Devuelve la ultima version cuyos datos han sido actualizados
    en mongo y calculadas sus estadisticas
    """
    current_version = db_metadata.get("last_calculated_patch")
    return current_version