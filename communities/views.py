from django.shortcuts import render, reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import CommunityForm
from .models import Community, Post


# Create your views here.
def index(request):
    communities = Community.objects.all()
    return render(request, 'communities/index.html', {'communities': communities})


def community(request, community_slug):
    community = Community.objects.get(slug=community_slug)
    posts = Post.objects.filter(community=community)

    return render(request, 'communities/community.html', {'posts': posts, 'community': community})


class CreateView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/create/'
    form = CommunityForm
    template_name = 'communities/create.html'

    def get(self, request):
        form = self.form()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form(request.POST)
        if form.is_valid():
            community = Community(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                creator=request.user,
                is_private=form.cleaned_data['is_private'],
                require_join_approval=form.cleaned_data['require_join_approval'],
            )
            community.save()

            return reverse(request, 'communities:community', kwargs={'community_slug': community.slug})
        return render(request, self.template_name, {'form': form})
