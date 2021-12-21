from django.urls import path, include
from django.conf.urls import url
from . import views


app_name = 'communities'
urlpatterns = [
    path('', views.community_list, name='community-list'),
    path('<slug:slug>/', views.community, name='community'),
    # path('ship-create-view/', views.CreateView.as_view(), name='ship-create-view'),
]