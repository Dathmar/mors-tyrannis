from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.index, name='list'),
    path('create/', views.CreateCommunityView.as_view(), name='create'),
    path('change-form-type/<str:form_type>/', views.change_form_type, name='change-form-type'),
    path('<slug:community_slug>/', views.view_community, name='detail'),
    path('<slug:community_slug>/edit/', views.EditCommunityView.as_view(), name='edit'),
    path('<slug:community_slug>/join/', views.JoinCommunityView.as_view(), name='join'),
    path('<slug:community_slug>/verify-join/', views.verify_join, name='join-verify'),
    path('<slug:community_slug>/new-post/', views.CreatePostView.as_view(), name='create-post'),
    path('<slug:community_slug>/comments/<int:post_id>/', views.post_view, name='view-post'),
    path('<slug:community_slug>/comments/<int:post_id>/edit/', views.EditPostView.as_view(), name='edit-post'),
    path('<slug:community_slug>/comments/<int:post_id>/add-comment/', views.AddCommentView.as_view(), name='post-add-comment'),
    path('<slug:community_slug>/comments/<int:post_id>/upvote/', views.upvote_post_comment, name='upvote-post'),
    path('<slug:community_slug>/comments/<int:post_id>/downvote/', views.downvote_post_comment, name='downvote-post'),
    path('<slug:community_slug>/comments/<int:post_id>/comment/<int:comment_id>/add-comment/', views.AddCommentView.as_view(), name='comment-add-comment'),
    path('<slug:community_slug>/comments/<int:post_id>/comment/<int:comment_id>/upvote/', views.upvote_post_comment, name='upvote-comment'),
    path('<slug:community_slug>/comments/<int:post_id>/comment/<int:comment_id>/downvote/', views.downvote_post_comment, name='downvote-comment'),

]
