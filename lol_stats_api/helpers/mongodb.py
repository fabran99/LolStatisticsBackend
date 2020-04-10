import pymongo
from django.conf import settings

def get_mongodb():
    """
    Devuelve conexion con mongodb
    """
    client = pymongo.MongoClient(
        host=settings.MONGO_DB_HOST,
        port=27017,
        connectTimeoutMS=8000, socketTimeoutMS=8000, serverSelectionTimeoutMS=30000, waitQueueTimeoutMS=8000,
        connect=False,
        tz_aware=True
    )
    mongodb = client.lol_app
    return mongodb


def get_saved_version():
    """
    Devuelve la ultima version cuyos datos han sido actualizados
    en mongo
    """
    current_system_data = get_mongodb().metadata.find_one({})
    if current_system_data is None:
        return None

    else:
        return current_system_data['current_version']