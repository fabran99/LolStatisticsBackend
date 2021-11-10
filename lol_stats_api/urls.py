from django.contrib import admin
from django.urls import path, include

app_name = "lol_stats_api"

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("assets/", include('assets.urls', namespace="assets_api")),
    path("stats/", include('stats.urls', namespace="stats_api")),
    path("extra_apis/", include('extra_apis.urls', namespace="extra_apis")),
]
