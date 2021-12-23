from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, 'users/index.html')


def view_user(request, username):
    return render(request, 'users/view_user.html')
