from django.shortcuts import render, reverse, get_object_or_404, HttpResponse, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .forms import CommunityForm, CommentForm, LinkPostForm, TextPostForm, ImagePostForm, JoinRequestForm
from .models import Community, Post, PostComment, CommunityMember, CommunityJoinRequest
from .voting.vote_functions import toggle_upvote, toggle_downvote, create_voting

from datetime import datetime
import logging
import json

logger = logging.getLogger('app_api')


# Create your views here.
def index(request):
    if request.user.is_authenticated:
        communities = Community.objects.filter(
            Q(is_private=False)
            | Q(id__in=CommunityMember.objects.filter(user=request.user).values_list('community__id', flat=True)))
    else:
        communities = Community.objects.filter(is_private=False)
    return render(request, 'communities/index.html', {'communities': communities})


def view_community(request, community_slug):
    community = Community.objects.get(slug=community_slug)
    if community.require_join_approval:
        if not community.is_member(request.user):
            return redirect(reverse('communities:request-join', kwargs={'community_slug': community_slug}))

    posts = Post.objects.filter(community=community)
    return render(request, 'communities/community.html', {'posts': posts,
                                                          'community': community,
                                                          'is_community_member': community.is_member(request.user),
                                                          'is_follower': community.is_follower(request.user)})


class RequestJoinView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/'
    form = JoinRequestForm
    template_name = 'communities/join-community.html'

    def get(self, request, *args, **kwargs):
        community_slug = kwargs.get('community_slug')
        community = get_object_or_404(Community, slug=community_slug)
        form = self.form()

        if CommunityJoinRequest.objects.filter(community=community, user=request.user).exists():
            return redirect(reverse('communities:request-join-done', kwargs={'community_slug': community_slug}))
        return render(request, self.template_name, {'form': form, 'community': community})

    def post(self, request, *args, **kwargs):
        community_slug = kwargs.get('community_slug')
        community = get_object_or_404(Community, slug=community_slug)
        form = self.form(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.user = request.user
            request_obj.community = community
            request_obj.save()
            return redirect(reverse('communities:request-join-done', kwargs={'community_slug': community_slug}))
        return render(request, self.template_name, {'form': form, 'community': community})


class ReviewJoinRequests(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/'
    template_name = 'communities/review-join-requests.html'

    def get(self, request, *args, **kwargs):
        community_slug = kwargs.get('community_slug')
        community = get_object_or_404(Community, slug=community_slug)
        status = kwargs.get('status', None)
        if status == 'accepted':
            join_requests = CommunityJoinRequest.objects.filter(community__slug=community_slug, is_approved=True,
                                                                is_rejected=False)
        elif status == 'rejected':
            join_requests = CommunityJoinRequest.objects.filter(community__slug=community_slug, is_approved=False,
                                                                is_rejected=True)
        else:
            join_requests = CommunityJoinRequest.objects.filter(community__slug=community_slug, is_approved=False,
                                                                is_rejected=False)

        return render(request, self.template_name, {'join_requests': join_requests,
                                                    'community': community,
                                                    'status': status})


def approve_join_request(request, community_slug, request_id):
    join_request = get_object_or_404(CommunityJoinRequest, id=request_id)
    try:
        join_request.approve_request()
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)


def reject_join_request(request, community_slug, request_id):
    join_request = get_object_or_404(CommunityJoinRequest, id=request_id)
    logger.info('joy in recjection')
    try:
        logger.info(request.body)
        data = json.loads(request.body)
        logger.info(data)
        reject_message = data.get('reject_message', None)
        logger.info(reject_message)
        join_request.reject_request(reject_message=reject_message)
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)


def join_complete(request, community_slug):
    community = get_object_or_404(Community, slug=community_slug)
    join_request = CommunityJoinRequest.objects.filter(community=community, user=request.user).first()
    return render(request, 'communities/join-community-done.html', {'community': community, 'join_request': join_request})


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
            member = CommunityMember(
                community=community,
                user=request.user,
                is_admin=True,
                is_owner=True,
                following=True,
            )
            member.save()

            return redirect(reverse('communities:detail', kwargs={'community_slug': community.slug}))
        return render(request, self.template_name, {'form': form})


class EditCommunityView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/'
    form = CommunityForm
    template_name = 'communities/create-community.html'

    def get(self, request, community_slug):
        community = get_object_or_404(Community, slug=community_slug)
        form = self.form(instance=community)
        return render(request, self.template_name, {'form': form, 'community': community, 'edit': True})

    def post(self, request, community_slug):
        form = self.form(request.POST)
        community = get_object_or_404(Community, slug=community_slug)
        if form.is_valid():
            community.name = form.cleaned_data['name']
            community.description = form.cleaned_data['description']
            community.is_private = form.cleaned_data['is_private']
            community.require_join_approval = form.cleaned_data['require_join_approval']

            community.save()

            return redirect(reverse('communities:detail', kwargs={'community_slug': community.slug}))
        return render(request, self.template_name, {'form': form, 'community': community, 'edit': True})


class JoinCommunityView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/join/'
    template_name = 'communities/join-community.html'

    def get(self, request, community_slug):
        return render(request, self.template_name)

    def post(self, request, community_slug):
        community = get_object_or_404(Community, slug=community_slug)
        community.add_follower(request.user)
        return redirect(reverse('communities:view', kwargs={'community_slug': community_slug}))


def verify_join(request, community_slug):
    logger.info(f'Verifying join request for {request.user}')
    community = get_object_or_404(Community, slug=community_slug)
    user = request.user
    if user.is_authenticated:
        if community.add_follower(user):
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False}, status=400)
    else:
        return JsonResponse({'status': 'Not Logged In'}, status=404)


def verify_unjoin(request, community_slug):
    logger.info(f'Verifying unjoin request for {request.user}')
    community = get_object_or_404(Community, slug=community_slug)
    user = request.user
    if user.is_authenticated:
        if community.remove_follower(user):
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False}, status=400)
    else:
        return JsonResponse({'status': 'Not Logged In'}, status=404)


def change_form_type(request, form_type):
    form = get_form_type(form_type)
    t = form.as_table()
    return JsonResponse({'form_html': t}, status=200)


def get_form_type(post_type, data=None, files=None, initial=None):
    if post_type == 'text':
        return TextPostForm(data=data, instance=initial)
    elif post_type == 'link':
        return LinkPostForm(data=data, instance=initial)
    elif post_type == 'image':
        return ImagePostForm(data=data, files=files, instance=initial)
    else:
        return None


class EditPostView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/'
    template_name = 'communities/create-post.html'

    def get(self, request, community_slug, post_id):
        post = get_object_or_404(Post, id=post_id)
        if post.user == request.user:
            form = get_form_type(post.post_type, initial=post)
            return render(request, self.template_name, {'form': form, 'post': post, 'edit': True})
        else:
            return HttpResponseBadRequest()

    def post(self, request, community_slug, post_id):
        post = get_object_or_404(Post, id=post_id)
        post_type = request.POST.get('post_type')
        if post.user == request.user:
            form = get_form_type(post_type, data=request.POST, files=request.FILES, initial=post)
            if form.is_valid():
                community = get_object_or_404(Community, slug=community_slug)
                post = get_post_object_from_form(user=request.user, community=community, form=form,
                                                 post_type=post_type, post=post)
                post.save()
                return redirect(reverse('communities:detail', kwargs={'community_slug': community_slug}))
            else:
                return HttpResponseBadRequest()
        else:
            return HttpResponseBadRequest()


def get_post_object_from_form(user, community, form, post_type, post=None):
    if post:
        edited_at = datetime.now()
    else:
        edited_at = None

    if post_type == 'link':
        if edited_at:
            post.title = form.cleaned_data['title']
            post.url = form.cleaned_data['url']
            post.post_type = post_type
            post.nsfw_flag = form.cleaned_data['nsfw_flag']
            post.edited_at = edited_at
            return post
        else:
            return Post.objects.create(
                title=form.cleaned_data['title'],
                url=form.cleaned_data['url'],
                user=user,
                community=community,
                post_type=post_type,
                nsfw_flag=form.cleaned_data['nsfw_flag'],
            )
    elif post_type == 'text':
        if edited_at:
            post.title = form.cleaned_data['title']
            post.content = form.cleaned_data['content']
            post.post_type = post_type
            post.nsfw_flag = form.cleaned_data['nsfw_flag']
            post.edited_at = edited_at
            return post
        else:
            return Post.objects.create(
                community=community,
                user=user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                post_type=post_type,
                nsfw_flag=form.cleaned_data['nsfw_flag'],
            )
    elif post_type == 'image':
        if edited_at:
            image = form.cleaned_data.get('image', None)
            logger.info(image)
            post.title = form.cleaned_data['title']
            if image:
                post.image = image
            post.post_type = post_type
            post.nsfw_flag = form.cleaned_data['nsfw_flag']
            post.edited_at = edited_at
            return post
        else:
            return Post.objects.create(
                title=form.cleaned_data['title'],
                user=user,
                community=community,
                image=form.cleaned_data.get('image'),
                post_type=post_type,
                nsfw_flag=form.cleaned_data['nsfw_flag'],
            )


class CreatePostView(LoginRequiredMixin, View):
    login_url = f'/accounts/login/?next=/c/new-post/'  # should learn how to use reverse here
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
        form = get_form_type(post_type, data=request.POST, files=request.FILES)
        if form.is_valid():
            community = get_object_or_404(Community, slug=community_slug)
            post = get_post_object_from_form(user=request.user, community=community, form=form,
                                             post_type=post_type)
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
        user = post_comment.user
    else:
        post_comment = None
        object_type = 'post'
        user = post.user

    rep_change = toggle_upvote(voting_user=request.user, post=post, post_comment=post_comment)
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

    rep_change = toggle_downvote(voting_user=request.user, post=post, post_comment=post_comment)
    data = {'rep_change': rep_change, 'vote_type': 'down', 'object_type': object_type}
    return JsonResponse(data, status=200)
