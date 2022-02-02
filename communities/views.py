from django.shortcuts import render, reverse, get_object_or_404, HttpResponse, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from .forms import CommunityForm, CommentForm, LinkPostForm, TextPostForm, ImagePostForm
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

    return render(request, 'communities/community.html', {'posts': posts,
                                                          'community': community,
                                                          'is_community_member': community.is_member(request.user)})


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

            return redirect(reverse('communities:detail', kwargs={'community_slug': community.slug}))
        return render(request, self.template_name, {'form': form})


class JoinCommunityView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/join/'
    template_name = 'communities/join-community.html'

    def get(self, request, community_slug):
        return render(request, self.template_name)

    def post(self, request, community_slug):
        community = get_object_or_404(Community, slug=community_slug)
        community.add_member(request.user)
        return redirect(reverse('communities:view', kwargs={'community_slug': community_slug}))


def verify_join(request, community_slug):
    logger.info(f'Verifying join request for {request.user}')
    community = get_object_or_404(Community, slug=community_slug)
    user = request.user
    if request.user.is_authenticated:
        if community.add_member(user):
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False}, status=400)
    else:
        return JsonResponse({'status': 'success'}, status=404)


def change_form_type(request, form_type):
    if form_type == 'text':
        form = TextPostForm()
    elif form_type == 'link':
        form = LinkPostForm()
    elif form_type == 'image':
        form = ImagePostForm()
    else:
        return HttpResponseBadRequest()
    t = form.as_table()
    return JsonResponse({'form_html': t}, status=200)


class CreatePostView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/new-post/' # should learn how to use reverse here
    link_form = LinkPostForm
    text_form = TextPostForm
    image_form = ImagePostForm
    template_name = 'communities/create-post.html'
    template_post_created = 'communities/index.html'

    def get(self, request, community_slug=None):
        image_form = self.image_form()
        return render(request, self.template_name, {'form': image_form})

    def post(self, request, community_slug):
        post_type = request.POST.get('post_type')
        if post_type == 'link':
            form = self.link_form(request.POST)
        elif post_type == 'text':
            form = self.text_form(request.POST)
        elif post_type == 'image':
            form = self.image_form(request.POST, request.FILES)
        else:
            return HttpResponseBadRequest()
        if form.is_valid():
            community = get_object_or_404(Community, slug=community_slug)
            if post_type == 'link':
                post = Post(
                    title=form.cleaned_data['title'],
                    url=form.cleaned_data['url'],
                    user=request.user,
                    community=community,
                    post_type=post_type,
                    nsfw_flag=form.cleaned_data['nsfw_flag'],
                )
            elif post_type == 'text':
                post = Post(
                    community=community,
                    user=request.user,
                    title=form.cleaned_data['title'],
                    content=form.cleaned_data['content'],
                    post_type=post_type,
                    nsfw_flag=form.cleaned_data['nsfw_flag'],
                )
            elif post_type == 'image':

                post = Post(
                    title=form.cleaned_data['title'],
                    user=request.user,
                    community=community,
                    image=form.cleaned_data.get('image'),
                    post_type=post_type,
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




