from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse
from time import sleep
from django.conf import settings
import os
from datetime import datetime as dt, timedelta as td
from .serializers import getMatchlistSerializer
from lol_stats_api.helpers.variables import SERVER_REAL_NAME_TO_ROUTE
from stats.riot_api_routes import get_matchlist_by_puuid_id, get_player_by_name
from lol_stats_api.helpers.redis import get_gameid, set_gameid

MAX_RETRIES = 5
MAX_TIME_TO_REFRESH = td(minutes=15)

STATS_API_KEY = os.getenv("STATS_API_KEY", None)

class LeagueAPIViewset(viewsets.ViewSet):
    def get_matchlist(self, request):
        print(request.META.get("Authorization"))
        auth = request.META.get("Authorization")
        if STATS_API_KEY is None or auth != STATS_API_KEY:
            return JsonResponse({"response":"Unauthorized"}, status=403)

        get_serializer = getMatchlistSerializer(data = request.GET)
        get_serializer.is_valid(raise_exception=True)
        limit = get_serializer.validated_data.get("limit")
        username = get_serializer.validated_data.get("username")
        region = get_serializer.validated_data.get("region")

        server = SERVER_REAL_NAME_TO_ROUTE[region]
        # Intento buscarlo en redis
        gameid_data = get_gameid(username, region)
        puuid = None
        player_games = None
        refreshed = False
        print(username)

        # chequeo si voy a buscarlo al endpoint
        if gameid_data is not None:
            puuid = gameid_data['puuid']
            if gameid_data['last_refresh'] > dt.utcnow()-MAX_TIME_TO_REFRESH:
                print(gameid_data['last_refresh'], dt.utcnow())
                player_games = gameid_data['player_games']
                print("uso los cacheados")


        #Si no lo tengo en cache
        if player_games is None:
            print("Entro a buscar cosas")
            # Busco el puuid
            if puuid is None:
                # Reintento si es necesario
                retries = 0
                while retries<MAX_RETRIES:
                    player_data = get_player_by_name(username, server, force_token=settings.INGAME_CALLS_API_KEY)
                    if player_data is not None:
                        puuid = player_data['puuid']
                        break
                    else:
                        retries+=1
                        sleep(0.5)

            # Busco la lista
            retries = 0
            while retries < MAX_RETRIES:
                player_games = get_matchlist_by_puuid_id(puuid, server, endIndex=limit, force_token=settings.INGAME_CALLS_API_KEY)
                if player_games is not None:
                    refreshed = dt.utcnow()
                    break 
                else:
                    retries +=1
                    sleep(0.5)
                
        
        if player_games is None:
            return JsonResponse({"data":"ERROR"}, status=500)
        
        if refreshed:
            set_gameid(username, region, {
                "puuid":puuid,
                "player_games": player_games,
                "last_refresh":refreshed
            })

        game_ids = [x.split("_")[1] for x in player_games]
        return JsonResponse(data={
            "game_ids": game_ids
        })


