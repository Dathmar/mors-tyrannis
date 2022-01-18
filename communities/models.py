from django.db import models
from django.utils.text import slugify
from django.shortcuts import reverse
from django.conf import settings
import logging
from users.models import UserMeta

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

    def save(self, *args, **kwargs):
        if not Post.objects.filter(pk=self.pk).exists():
            PostCommentLike.add_upvote(self.user, self)

        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def add_like(self):
        self.like_count += 1
        self.save()

    def add_dislike(self):
        self.dislike_count += 1
        self.save()

    def remove_like(self):
        self.like_count -= 1
        self.save()

    def remove_dislike(self):
        self.dislike_count -= 1
        self.save()

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

    def add_like(self):
        self.like_count += 1
        self.save()

    def add_dislike(self):
        self.dislike_count += 1
        self.save()

    def remove_like(self):
        self.like_count -= 1
        self.save()

    def remove_dislike(self):
        self.dislike_count -= 1
        self.save()

    def save(self, *args, **kwargs):
        # if this is a new comment then add 1 to the comment count for the post.
        if not PostComment.objects.filter(id=self.id).exists():
            self.post.comment_count += 1
            self.post.save()
            PostCommentLike.add_upvote(self.user, self.post, self)

        super(PostComment, self).save(*args, **kwargs)

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
    def add_rep(rep_val, post, post_comment=None):
        if post_comment:
            community = post_comment.community
            user = post_comment.user
        else:
            community = post.community
            user = post.user

        community_member = CommunityMember.objects.get(community=community, user=user)
        user_meta = UserMeta.objects.get(user=user)
        logger.info(f'{user.username} has {community_member.community_rep} rep for {community.name}')
        community_member.add_community_rep(rep_val)
        user_meta.add_reputation(rep_val)

    class Meta:
        unique_together = ('user', 'post', 'post_comment')

    @staticmethod
    def toggle_upvote(user, post, post_comment=None):
        if post_comment:
            obj = post_comment
        else:
            obj = post

        logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')

        if PostCommentLike.remove_downvote_if_exists(user=user, post=post, post_comment=post_comment):
            if post_comment:
                logger.info(f'refresh post comment from db')
                post_comment.refresh_from_db
            else:
                logger.info(f'refresh post from db')
                post.refresh_from_db
        if not PostCommentLike.remove_upvote_if_exists(user=user, post=post, post_comment=post_comment):
            PostCommentLike.add_upvote(user=user, post=post, post_comment=post_comment)

        logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')

    @staticmethod
    def toggle_downvote(user, post, post_comment=None):
        if post_comment:
            obj = post_comment
        else:
            obj = post

        logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
        if PostCommentLike.remove_upvote_if_exists(user=user, post=post, post_comment=post_comment):
            if post_comment:
                logger.info(f'refresh post comment from db')
                post_comment.refresh_from_db
            else:
                logger.info(f'refresh post from db')
                post.refresh_from_db
        if not PostCommentLike.remove_downvote_if_exists(user=user, post=post, post_comment=post_comment):
            PostCommentLike.add_downvote(user=user, post=post, post_comment=post_comment)

        logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')

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
        PostCommentLike.add_rep(1, post, post_comment)

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
        PostCommentLike.add_rep(-1, post, post_comment)

    @staticmethod
    def remove_upvote_if_exists(user, post, post_comment=None):
        if post_comment:
            pcl = PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=True)
        else:
            pcl = PostCommentLike.objects.filter(user=user, post=post, upvote=True)

        if pcl.exists():
            logger.info(f'Removing upvote for {user.username} on post {post.id}')
            pcl.first().delete()
            PostCommentLike.add_rep(-1, post, post_comment)
            return True

        return False

    @staticmethod
    def remove_downvote_if_exists(user, post, post_comment=None):
        if post_comment:
            pcl = PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=False)
        else:
            pcl = PostCommentLike.objects.filter(user=user, post=post, upvote=False)

        if pcl.exists():
            logger.info(f'Removing downvote for {user.username} on post {post.id}')
            pcl.first().delete()
            PostCommentLike.add_rep(1, post, post_comment)
            return True

        return False

    def save(self, *args, **kwargs):
        if not PostCommentLike.objects.filter(id=self.id).exists():
            logger.info(f'Adding PCL {self.user.username} on post {self.post} and post_comment {self.post_comment}')
            if self.post_comment:
                obj = self.post_comment
            else:
                obj = self.post

            if self.upvote:
                logger.info(f'Adding like count for {self.user.username} on post {self.post}')
                logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
                obj.add_like()
                obj.refresh_from_db
                logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
            else:
                logger.info(f'Adding dislike count for {self.user.username} on post {self.post}')
                logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
                obj.add_dislike()
                obj.refresh_from_db
                logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')

        super(PostCommentLike, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        logger.info(f'Deleting post_comment_like {self.id} for {self.user.username} on post {self.post} and post_comment {self.post_comment}')
        if self.post_comment:
            obj = self.post_comment
        else:
            obj = self.post

        if self.upvote:
            logger.info(f'subtracting like count for {self.user.username} on post {self.post}')
            logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
            obj.remove_like()
            obj.refresh_from_db
            logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
        else:
            logger.info(f'subtracting dislike count for {self.user.username} on post {self.post}')
            logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')
            obj.remove_dislike()
            obj.refresh_from_db
            logger.info(f'{type(obj)} {obj} like count - {obj.like_count} - dislike count - {obj.dislike_count}')

        super(PostCommentLike, self).delete(*args, **kwargs)


