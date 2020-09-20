from django.urls import path
from . import views

app_name = "stats"

urlpatterns = [
    path('runes/by_id', views.GetRunesByChampId.as_view({"get":"get"}))
]