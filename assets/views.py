from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit

from .serializers import *
from .business import get_main_list

class MainListView(viewsets.ViewSet):
    @ratelimit(key='ip', rate='10/minute')
    def get(self, request):
        return get_main_list()

