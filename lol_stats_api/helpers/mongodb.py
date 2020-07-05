import pymongo
from django.conf import settings
from monary import Monary

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
    current_system_data = get_mongo_assets().metadata.find_one({})
    if current_system_data is None:
        return None

    else:
        return current_system_data['current_version']