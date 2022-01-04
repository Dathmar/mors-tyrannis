from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.index, name='list'),
    path('create/', views.CreateView.as_view(), name='create'),
    path('<slug:community_slug>/', views.community, name='detail'),
    # path('ship-create-view/', views.CreateView.as_view(), name='ship-create-view'),
]