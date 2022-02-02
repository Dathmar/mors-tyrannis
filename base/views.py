from django.shortcuts import render
from django.views import View

from communities.models import Post


def index(request):
    posts = Post.objects.all()[:20]
    return render(request, 'base/index.html', {'posts': posts})
