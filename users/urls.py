from django.urls import path, include
from . import views


app_name = 'users'
urlpatterns = [
    path('', views.index, name='user-index'),
    path('notifications/', views.NotificationCenterView.as_view(), name='notifications'),
    path('<str:username>/', views.view_user, name='view-user'),
    # path('ship-create-view/', views.CreateView.as_view(), name='ship-create-view'),
]