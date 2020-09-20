from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse

from .serializers import GetRuneByID
from .business import get_champ_runes

class GetRunesByChampId(viewsets.ViewSet):
    def get(self, request):
        serializer = GetRuneByID(data = request.GET)
        serializer.is_valid(raise_exception=True)

        id = serializer.validated_data.get('id')
        elo = serializer.validated_data.get('elo')

        if not elo:
            elo = "high_elo"

        return get_champ_runes(id, elo)