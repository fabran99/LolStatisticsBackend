from lol_stats_api.helpers.mongodb import get_mongo_stats
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

statsDb = get_mongo_stats()

def get_champ_runes(id, elo):
    # Pido las estadisticas de el champ seleccionado
    field = 'champInfo.{}.runes'.format(elo)
    runes = statsDb.stats_by_champ.find_one({"championId":int(id)},{
        field:1,
        "_id":0,
        "champName":1
        })
    
    if runes:
        return JsonResponse({"runes":runes['champInfo'][elo]['runes'], "champName":runes['champName']})
    
    return Response(data={"error":"No se encontro el campeon solicitado"}, status=status.HTTP_404_NOT_FOUND)
    
    
