from django.urls import path, include
from . import views


app_name = 'communities'
urlpatterns = [
    path('', views.index, name='community-list'),
    path('<slug:slug>/', views.community, name='community'),
    # path('ship-create-view/', views.CreateView.as_view(), name='ship-create-view'),
]