from django.urls import path
from . import views

app_name = "stats"

urlpatterns = [
    path('player_matchlist/', views.LeagueAPIViewset.as_view({"get":"get_matchlist"}))
]
