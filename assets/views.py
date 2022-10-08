from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse

from .serializers import *
from .business import get_main_list

class MainListView(viewsets.ViewSet):
    def get(self, request):
        return get_main_list()

