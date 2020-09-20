from redis import Redis
import os

if os.getenv("IS_PROD"):
    db_metadata = Redis(host=os.getenv("REDIS_METADATA_HOST"),
                        db=os.getenv("REDIS_METADATA_DB"), password=os.getenv("REDIS_METADATA_PASSWORD"), decode_responses=True)
else:
    db_metadata = Redis(host=os.getenv("REDIS_METADATA_HOST"),
                        db=os.getenv("REDIS_METADATA_DB"), decode_responses=True)

db_matchlist = Redis(db=os.getenv("REDIS_GAMELIST_DB"),
                     decode_responses=True)
db_processed_match = Redis(db=os.getenv("REDIS_GAMEID_PROCESSED_DB"))
db_celery = Redis(db=os.getenv("CELERY_DB"), decode_responses=True)
