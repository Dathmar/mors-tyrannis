from django.shortcuts import render, reverse, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import CommunityForm, PostForm
from .models import Community, Post


# Create your views here.
def index(request):
    communities = Community.objects.all()
    return render(request, 'communities/index.html', {'communities': communities})


def view_community(request, community_slug):
    community = Community.objects.get(slug=community_slug)
    posts = Post.objects.filter(community=community)

    return render(request, 'communities/community.html', {'posts': posts, 'community': community})


class CreateCommunityView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/create/'
    form = CommunityForm
    template_name = 'communities/create-community.html'

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


class CreatePostView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/new-post/' # should learn how to use reverse here
    form = PostForm
    template_name = 'communities/create-post.html'
    template_post_created = 'communities/index.html'

    def get(self, request, community_slug=None):
        form = self.form()
        return render(request, self.template_name, {'form': form})

    def post(self, request, community_slug):
        form = self.form(request.POST)
        if form.is_valid():
            community = get_object_or_404(Community, slug=community_slug)
            post = Post(
                community=community,
                user=request.user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                post_type=form.cleaned_data['post_type'],
                nsfw_flag=form.cleaned_data['nsfw_flag'],
            )
            post.save()

            return view_community(request, community_slug)

        return render(request, self.template_name, {'form': form})
