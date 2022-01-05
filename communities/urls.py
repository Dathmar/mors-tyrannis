from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.index, name='list'),
    path('<slug:community_slug>/', views.view_community, name='detail'),
    path('<slug:community_slug>/new-post/', views.CreatePostView.as_view(), name='create-post'),
    path('create/', views.CreateCommunityView.as_view(), name='create'),
    # path('ship-create-view/', views.CreateView.as_view(), name='ship-create-view'),
]