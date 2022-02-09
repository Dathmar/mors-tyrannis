from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path(
        'change-password/', auth_views.PasswordChangeView.as_view(
            template_name='registration/change-password.html',
            success_url='/accounts/password-change-done/',
        ), name='change_password'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password-change-done.html'), name='password_change_done'),

]
