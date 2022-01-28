from django.shortcuts import render, reverse, get_object_or_404, HttpResponse, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .forms import CommunityForm, PostForm, CommentForm
from .models import Community, Post, PostComment

from .voting.vote_functions import toggle_upvote, toggle_downvote, create_voting

import json
import logging

logger = logging.getLogger('app_api')


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

            return reverse(request, 'communities:index', kwargs={'community_slug': community.slug})
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
            create_voting(request.user, post)

            return redirect('communities:detail', community_slug=community.slug)

        return render(request, self.template_name, {'form': form})


class AddCommentView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/'  # need to route back to the specific post/comment
    form = CommentForm
    template_name = 'communities/create-comment.html'

    def get(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        comment_id = kwargs.get('comment_id', None)
        form = self.form()

        if comment_id:
            comment_context = get_object_or_404(PostComment, id=comment_id)
        else:
            comment_context = get_object_or_404(Post, id=post_id)

        return render(request, self.template_name, {'comment_context': comment_context, 'form': form})

    def post(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        comment_id = kwargs.get('comment_id', None)
        form = self.form(request.POST)

        if form.is_valid():
            parent_comment = None
            if comment_id:
                parent_comment = get_object_or_404(PostComment, id=comment_id)

            post = get_object_or_404(Post, id=post_id)

            comment = PostComment.objects.create(
                post=post,
                community=post.community,
                user=request.user,
                parent_comment=parent_comment,
                content=form.cleaned_data['content'],
            )
            comment.save()
            create_voting(request.user, post, comment)

            return redirect('communities:view-post', community_slug=post.community.slug, post_id=post_id)

        if comment_id:
            comment_context = get_object_or_404(PostComment, id=comment_id)
        else:
            comment_context = get_object_or_404(Post, id=post_id)
        return render(request, self.template_name, {'comment_context': comment_context, 'form': form})


def post_view(request, *args, **kwargs):
    post = get_object_or_404(Post, id=kwargs['post_id'])
    post_comments = PostComment.objects.filter(post=post)

    return render(request, 'communities/view-post.html', {'post': post, 'post_comments': post_comments})


@login_required
def upvote_post_comment(request, *args, **kwargs):
    post = get_object_or_404(Post, id=kwargs['post_id'])
    if 'comment_id' in kwargs.keys():
        post_comment = get_object_or_404(PostComment, id=kwargs['comment_id'])
        object_type = 'comment'
    else:
        post_comment = None
        object_type = 'post'

    rep_change = toggle_upvote(user=request.user, post=post, post_comment=post_comment)
    data = {'rep_change': rep_change, 'vote_type': 'up', 'object_type': object_type}
    return JsonResponse(data, status=200)


@login_required
def downvote_post_comment(request, *args, **kwargs):
    post = get_object_or_404(Post, id=kwargs['post_id'])
    if 'comment_id' in kwargs.keys():
        post_comment = get_object_or_404(PostComment, id=kwargs['comment_id'])
        object_type = 'comment'
    else:
        post_comment = None
        object_type = 'post'

    rep_change = toggle_downvote(user=request.user, post=post, post_comment=post_comment)
    data = {'rep_change': rep_change, 'vote_type': 'down', 'object_type': object_type}
    return JsonResponse(data, status=200)




