from django.urls import path

from django101.common.views import index

urlpatterns = [
    path('', index, name="index"),
]
