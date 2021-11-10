from django.urls import path
from . import views

app_name = "extra_apis"

urlpatterns = [
    path('extra/', views.ExtraView.as_view({"get":"get"}))
]
