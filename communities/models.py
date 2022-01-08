import random

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

    def save(self, *args, **kwargs):
        # if this is a new comment then add 1 to the comment count for the post.
        if not PostComment.objects.filter(id=self.id).exists():
            self.post.comment_count += 1
            self.post.save()

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

    @staticmethod
    def toggle_upvote(user, post, post_comment=None):
        logger.info(f'Post {post.id} downvotes = {post.dislike_count} upvotes = {post.like_count}')
        if PostCommentLike.upvote_exists(user=user, post=post, post_comment=post_comment):  # if an upvote exists then delete it
            logger.info(f'Upvote exists for {user.username} on post {post.id}')
            PostCommentLike.remove_upvote(user=user, post=post, post_comment=post_comment)
        else:
            logger.info(f'Upvote does not exist for {user.username} on post {post.id}')
            PostCommentLike.add_upvote(user=user, post=post, post_comment=post_comment)

        if PostCommentLike.downvote_exists(user=user, post=post, post_comment=post_comment):  # if a downvote exists then delete it
            logger.info(f'Downvote exists for {user.username} on post {post.id}')
            PostCommentLike.remove_downvote(user=user, post=post, post_comment=post_comment)
        logger.info(f'Post {post.id} downvotes = {post.dislike_count} upvotes = {post.like_count}')

    @staticmethod
    def toggle_downvote(user, post, post_comment=None):
        logger.info(f'Post {post.id} downvotes = {post.dislike_count} upvotes = {post.like_count}')
        if PostCommentLike.downvote_exists(user=user, post=post, post_comment=post_comment):  # if an upvote exists then delete it
            logger.info(f'Downvote exists for {user.username} on post {post.id}')
            PostCommentLike.remove_downvote(user=user, post=post, post_comment=post_comment)
        else:
            logger.info(f'Downvote does not exist for {user.username} on post {post.id}')
            PostCommentLike.add_downvote(user=user, post=post, post_comment=post_comment)

        if PostCommentLike.upvote_exists(user=user, post=post, post_comment=post_comment):  # if an upvote exists then delete it
            logger.info(f'Upvote exists for {user.username} on post {post.id}')
            PostCommentLike.remove_upvote(user=user, post=post, post_comment=post_comment)
        logger.info(f'Post {post.id} downvotes = {post.dislike_count} upvotes = {post.like_count}')

    @staticmethod
    def upvote_exists(user, post, post_comment=None):
        if post_comment:
            logger.info(f'Checking if upvote exists for {user.username} on post {post.id} and post_comment {post_comment.id}')
            logger.info(f'Upvote exists: {PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=True).exists()}')
            return PostCommentLike.objects.filter(user=user, post=post,
                                                  post_comment=post_comment, upvote=True).exists()
        else:
            logger.info(f'Checking if upvote exists for {user.username} on post {post.id}')
            logger.info(f'Upvote exists: {PostCommentLike.objects.filter(user=user, post=post, upvote=True).exists()}')
            return PostCommentLike.objects.filter(user=user, post=post,
                                                  upvote=True).exists()

    @staticmethod
    def downvote_exists(user, post, post_comment=None):
        if post_comment:
            logger.info(f'Checking if downvote exists for {user.username} on post {post.id} and post_comment {post_comment.id}')
            logger.info(f'Downvote exists: {PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=False).exists()}')
            return PostCommentLike.objects.filter(user=user, post=post,
                                                  post_comment=post_comment, upvote=False).exists()
        else:
            logger.info(f'Checking if downvote exists for {user.username} on post {post.id}')
            logger.info(f'Downvote exists: {PostCommentLike.objects.filter(user=user, post=post, upvote=False).exists()}')
            return PostCommentLike.objects.filter(user=user, post=post,
                                                  upvote=False).exists()

    @staticmethod
    def add_upvote(user, post, post_comment=None):
        logger.info(f'Adding upvote for {user.username} on post {post.id}')
        post_comment_like = PostCommentLike.objects.create(
            user=user,
            upvote=True,
            post=post,
            post_comment=post_comment
        )
        post_comment_like.save()

    @staticmethod
    def add_downvote(user, post, post_comment=None):
        logger.info(f'Adding downvote for {user.username} on post {post.id}')
        post_comment_like = PostCommentLike.objects.create(
            user=user,
            upvote=False,
            post=post,
            post_comment=post_comment
        )
        post_comment_like.save()

    @staticmethod
    def remove_upvote(user, post, post_comment=None):
        if post_comment:
            logger.info(f'Removing upvote for {user.username} on post {post.id} and post_comment {post_comment.id}')
            PostCommentLike.objects.get(user=user, post=post,
                                           post_comment=post_comment, upvote=True).delete()
        else:
            logger.info(f'Removing upvote for {user.username} on post {post.id}')
            PostCommentLike.objects.get(user=user, post=post,
                                           upvote=True).delete()

    @staticmethod
    def remove_downvote(user, post, post_comment=None):
        if post_comment:
            logger.info(f'Removing downvote for {user.username} on post {post.id} and post_comment {post_comment.id}')
            PostCommentLike.objects.get(user=user, post=post,
                                           post_comment=post_comment, upvote=False).delete()
        else:
            logger.info(f'Removing downvote for {user.username} on post {post.id}')
            PostCommentLike.objects.get(user=user, post=post,
                                           upvote=False).delete()

    def save(self, *args, **kwargs):
        if not PostCommentLike.objects.filter(id=self.id).exists():
            if self.upvote:
                if self.post_comment:
                    self.post_comment.like_count += 1
                    self.post_comment.save()
                else:
                    self.post.like_count += 1
                    self.post.save()
            else:
                if self.post_comment:
                    self.post_comment.dislike_count += 1
                    self.post_comment.save()
                else:
                    self.post.dislike_count += 1
                    self.post.save()

        super(PostCommentLike, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.info(f'Deleting post_comment_like {self.id}')
        if self.upvote:
            if self.post_comment:
                self.post_comment.like_count -= 1
                self.post_comment.save()
            else:
                self.post.like_count -= 1
                self.post.save()
        else:
            if self.post_comment:
                self.post_comment.dislike_count -= 1
                self.post_comment.save()
            else:
                self.post.dislike_count -= 1
                self.post.save()

        super(PostCommentLike, self).delete(*args, **kwargs)


