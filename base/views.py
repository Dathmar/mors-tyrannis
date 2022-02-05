from django.shortcuts import render

from communities.models import Post, CommunityMember


def index(request):
    posts = None
    if request.user.is_authenticated:
        communities = CommunityMember.objects.filter(user=request.user, following=True).values_list('community', flat=True)
        posts = Post.objects.filter(community__in=communities)[:20]
    return render(request, 'base/index.html', {'posts': posts})
