from django.db import models
from django.utils.text import slugify
from django.shortcuts import reverse
from django.conf import settings

import logging

logger = logging.getLogger('app_api')


# Create your models here.
class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False) # hidden from front page
    require_join_approval = models.BooleanField(default=False) # only members can post

    slug = models.SlugField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('community_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(Community, self).save(*args, **kwargs)


class CommunityJoinRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    message = models.TextField()

    is_approved = models.BooleanField(default=False)
    reject_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.community}"

    def approve_request(self):
        self.is_approved = True
        self.save()

    def reject_request(self, reject_message):
        self.is_approved = False
        self.reject_message = reject_message
        self.save()


class CommunityMember(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    community_rep = models.IntegerField(default=0)

    is_admin = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('community', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.community.name}'

    def add_community_rep(self, rep):
        self.community_rep += rep
        self.save()


class UserExtension(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site_rep = models.IntegerField(default=0)


class CommunityBans(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    ban_reason = models.TextField(blank=True, null=True)
    ban_expiry = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Post(models.Model):
    post_types = ((0, 'text'), (1, 'image'), (2, 'link'), (3, 'poll'))

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    content = models.TextField()

    post_type = models.IntegerField(choices=post_types, default=0)

    nsfw_flag = models.BooleanField(default=False)

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    comment_count = models.IntegerField(default=0)

    is_sticky = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('communities:view-post', kwargs=({'post_id': self.id, 'community_slug': self.community.slug}))

    def get_upvote_url(self):
        return reverse('communities:upvote-post', kwargs=({'post_id': self.id, 'community_slug': self.community.slug}))

    def get_downvote_url(self):
        return reverse('communities:downvote-post', kwargs=({'post_id': self.id, 'community_slug': self.community.slug}))

    def total_rep(self):
        return self.like_count - self.dislike_count


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content

    def get_absolute_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}'

    def get_upvote_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/upvote'

    def get_downvote_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/downvote'

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
