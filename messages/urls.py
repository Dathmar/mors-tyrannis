from django.urls import path, include
from . import views


app_name = 'messages'
urlpatterns = [
    path('', views.index, name='index'),
]