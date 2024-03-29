from redis import Redis
import os
import pickle

if os.getenv("IS_PROD"):
    db_metadata = Redis(host=os.getenv("REDIS_METADATA_HOST"),
                        db=os.getenv("REDIS_METADATA_DB"), password=os.getenv("REDIS_METADATA_PASSWORD"), decode_responses=True)
    db_gameids = Redis(db=os.getenv("REDIS_GAMEID_LIST_DB"), host=os.getenv("REDIS_GAMEID_LIST_HOST") ,password=os.getenv("REDIS_METADATA_PASSWORD"))
else:
    db_metadata = Redis(host=os.getenv("REDIS_METADATA_HOST"),
                        db=os.getenv("REDIS_METADATA_DB"), decode_responses=True)
    db_gameids = Redis(db=os.getenv("REDIS_GAMEID_LIST_DB"), host=os.getenv("REDIS_GAMEID_LIST_HOST"))

db_matchlist = Redis(host = os.getenv("REDIS_GAMELIST_HOST"), db=os.getenv("REDIS_GAMELIST_DB"),
                     decode_responses=True)
db_processed_match = Redis(host = os.getenv("REDIS_GAMEID_PROCESSED_HOST"),db=os.getenv("REDIS_GAMEID_PROCESSED_DB"))
db_celery = Redis(host =os.getenv("CELERY_HOST"), db=os.getenv("CELERY_DB"), decode_responses=True)


# ID de partidas por endpoint

def get_gameid(username, region):
    data = db_gameids.get("{}:{}".format(username, region))
    if data is not None:
        data = pickle.loads(data)
    return data

def set_gameid(username, region, data):
    db_gameids.set("{}:{}".format(username, region), pickle.dumps(data), ex=60*60*24*10)