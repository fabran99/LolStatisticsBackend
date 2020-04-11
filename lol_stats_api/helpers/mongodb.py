import pymongo
from django.conf import settings

def get_mongo_assets():
    """
    Devuelve conexion con mongodb de assets
    """
    client = pymongo.MongoClient(
        host=settings.MONGO_DB_HOST,
        port=27017
    )
    mongodb = client.assets
    return mongodb

def get_mongo_data():
    """
    Devuelve conexion con mongodb de datos
    """
    client = pymongo.MongoClient(
        host=settings.MONGO_DB_HOST,
        port=27017
    )
    mongodb = client.lol_data
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