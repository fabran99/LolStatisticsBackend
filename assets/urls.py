from django.urls import path
from . import views

app_name = "assets"

urlpatterns = [
    path('main_list/', views.MainListView.as_view({"get":"get"}))
]