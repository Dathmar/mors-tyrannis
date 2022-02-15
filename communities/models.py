from django.db import models
from django.utils.text import slugify
from django.shortcuts import reverse
from django.conf import settings

import logging
import re

logger = logging.getLogger('app_api')


# Create your models here.
class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_private = models.BooleanField(default=False)  # hidden from front page
    require_join_approval = models.BooleanField(default=False)  # only members can post

    slug = models.SlugField(max_length=100, unique=True)

    auto_follow = models.BooleanField(default=False)  # automatically follow this community on account creation

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'communities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('community_detail', kwargs={'slug': self.slug})

    def has_access(self, user):
        if self.require_join_approval:
            if user.is_anonymous:
                return False
            if self.is_member(user):
                return True
            return CommunityJoinRequest.objects.filter(community=self, user=user, is_approved=True).exists()
        return True

    def is_member(self, user):
        if user.is_authenticated:
            return CommunityMember.objects.filter(community=self, user=user).exists()
        return False

    def is_admin(self, user):
        if user.is_authenticated:
            return CommunityMember.objects.filter(community=self, user=user, is_admin=True).exists()

    def is_follower(self, user):
        if user.is_authenticated:
            return CommunityMember.objects.filter(community=self, user=user, following=True).exists()
        return False

    def add_member(self, user):
        if not self.is_member(user):
            member = CommunityMember.objects.create(community=self, user=user)
            member.save()
            return True
        return False

    def add_follower(self, user):
        if not self.is_member(user):
            member = CommunityMember.objects.create(community=self, user=user, following=True)
            member.save()
            return True

        if not self.is_follower(user):
            member = CommunityMember.objects.get(community=self, user=user)
            member.following = True
            member.save()
            return True
        return False

    def remove_follower(self, user):
        if not self.is_member(user):
            return True

        if self.is_follower(user):
            member = CommunityMember.objects.get(community=self, user=user)
            member.following = False
            member.save()
            return True

        return False

    def has_join_requests(self):
        return CommunityJoinRequest.objects.filter(community=self, is_rejected=False, is_approved=False).exists()

    def save(self, *args, **kwargs):
        if not Community.objects.filter(id=self.id).exists():
            self.slug = slugify(self.name)

        super(Community, self).save(*args, **kwargs)


class CommunityJoinRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    message = models.TextField()

    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    reject_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.community}"

    def approve_request(self):
        if not CommunityMember.objects.filter(community=self.community, user=self.user).exists():
            cm = CommunityMember.objects.create(community=self.community, user=self.user)
            cm.save()

        self.is_approved = True
        self.is_rejected = False
        self.save()

    def reject_request(self, reject_message):
        self.is_approved = False
        self.is_rejected = True
        self.reject_message = reject_message
        self.save()

    def get_approval_url(self):
        return reverse('communities:approve-join-request',
                       kwargs={'community_slug': self.community.slug, 'request_id': self.id})

    def get_rejection_url(self):
        return reverse('communities:reject-join-request',
                       kwargs={'community_slug': self.community.slug, 'request_id': self.id})


class CommunityMember(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    community_rep = models.IntegerField(default=0)

    is_admin = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    following = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('community', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.community.name}'

    def add_community_rep(self, rep):
        self.community_rep += rep
        self.save()


class CommunityBans(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    ban_reason = models.TextField(blank=True, null=True)
    ban_expiry = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def post_image_location(instance, filename):
    return f'post_images/{instance.community.slug}/{instance.id}/{filename}'


class Post(models.Model):
    post_types = (('image', 'Image'), ('text', 'Text'), ('link', 'Link'))

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=post_image_location, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    post_type = models.CharField(max_length=5, choices=post_types, default='image')
    nsfw_flag = models.BooleanField(default=False)

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    is_sticky = models.BooleanField(default=False)

    edited_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def comment_count(self):
        return PostComment.objects.filter(post=self).count()

    def has_user_upvote(self, user):
        if user.is_authenticated and CommunityMember.objects.filter(community=self.community, user=user).exists():
            pcl = PostCommentLike.objects.filter(post=self, user=user, post_comment=None, upvote=True)
            if pcl.exists():
                pcl = pcl.first()
                if pcl.upvote:
                    return True
        return False

    def has_user_downvote(self, user):
        if user.is_authenticated and CommunityMember.objects.filter(community=self.community, user=user).exists():
            pcl = PostCommentLike.objects.filter(post=self, user=user, post_comment=None, upvote=False)
            if pcl.exists():
                pcl = pcl.first()
                if pcl.upvote:
                    return True
        return False

    def get_absolute_url(self):
        return reverse('communities:view-post', kwargs=({'post_id': self.id, 'community_slug': self.community.slug}))

    def get_upvote_url(self):
        return reverse('communities:upvote-post', kwargs=({'post_id': self.id, 'community_slug': self.community.slug}))

    def get_downvote_url(self):
        return reverse('communities:downvote-post', kwargs=({'post_id': self.id,
                                                             'community_slug': self.community.slug}))

    def total_rep(self):
        return self.like_count - self.dislike_count

    def get_embed(self):
        if self.post_type == 'link':
            if 'youtube' in self.url:
                return f'<iframe width="100%" height="100%" ' \
                       f'src="{you_tube_embed_url(self.url)}" title="YouTube video player" ' \
                       f'frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; ' \
                       f'gyroscope; picture-in-picture" allowfullscreen></iframe>'
        return None


def you_tube_embed_url(video_url):
    regex = r"(?:https:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.+)"
    return re.sub(regex, r"https://www.youtube.com/embed/\1", video_url)


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    content = models.TextField()

    edited_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content

    def has_user_upvote(self, user):
        if user.is_authenticated and CommunityMember.objects.filter(community=self.community, user=user).exists():
            pcl = PostCommentLike.objects.filter(post=self.post, user=user, post_comment=self, upvote=True)
            if pcl.exists():
                pcl = pcl.first()
                if pcl.upvote:
                    return True
        return False

    def has_user_downvote(self, user):
        if user.is_authenticated and CommunityMember.objects.filter(community=self.community, user=user).exists():
            pcl = PostCommentLike.objects.filter(post=self.post, user=user, post_comment=self, upvote=False)
            if pcl.exists():
                pcl = pcl.first()
                if pcl.upvote:
                    return True
        return False

    def get_absolute_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/'

    def get_upvote_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/upvote/'

    def get_downvote_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/downvote/'

    def total_rep(self):
        return self.like_count - self.dislike_count


class PostCommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, blank=True, null=True)
    upvote = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        unique_together = ('user', 'post', 'post_comment')
