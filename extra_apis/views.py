from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse
import pickle

from .serializers import *
from redis import Redis 
import os

db_extra_data = Redis(host=os.getenv("REDIS_EXTRA_DATA_HOST", 'localhost'),
                        db=os.getenv("REDIS_EXTRA_DATA_DB", '0'), password=os.getenv("REDIS_METADATA_PASSWORD", "0"), decode_responses=True)
def get_all_from_redis():
    response = {}

    for key in db_extra_data.keys():
        try:
            response[key] = pickle.loads(db_extra_data.get(key))
        except Exception as e:
            print(e)
    return response

class MainListView(viewsets.ViewSet):
    def get(self, request):
        response = get_all_from_redis()

        return JsonResponse(response)
