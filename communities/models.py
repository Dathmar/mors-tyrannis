from django.db import models
from django.utils.text import slugify
from django.conf import settings


# Create your models here.
class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_private = models.BooleanField(default=False)

    slug = models.SlugField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    content = models.TextField()

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    is_sticky = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/c/{self.community.slug}/comments/{self.id}'

    def get_like_url(self):
        return f'/c/{self.community.slug}/comments/{self.id}/like'

    def get_unlike_url(self):
        return f'/c/{self.community.slug}/comments/{self.id}/unlike'

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

    def get_like_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/like'

    def get_unlike_url(self):
        return f'/c/{self.community.slug}/comments/{self.post.id}/comment/{self.id}/unlike'

    def total_rep(self):
        return self.like_count - self.dislike_count


class PostCommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, blank=True, null=True)
    upvote = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def add_upvote(self, post, post_comment=None):
        self.post = post
        self.post_comment = post_comment

        # if this is a post comment then add the rep to the comment
        if self.post_comment:
            self.post_comment.like_count += 1
            self.post_comment.save()
        else: # otherwise add the rep to the post
            self.post.like_count += 1
            self.post.save()

        if not self.upvote_exists():
            self.save()

        if self.downvote_exists():
            self.remove_downvote()

            if self.post_comment:
                self.post_comment.dislike_count -= 1
                self.post_comment.save()
            else:
                self.post.dislike_count -= 1
                self.post.save()

    def add_downvote(self, post, post_comment=None):
        self.post = post
        self.post_comment = post_comment

        if self.post_comment:
            self.post_comment.dislike_count += 1
            self.post_comment.save()
        else:
            self.post.dislike_count += 1
            self.post.save()

        if not self.downvote_exists():
            self.save()

        if self.upvote_exists():
            if post_comment:
                self.post_comment.like_count -= 1
                self.post_comment.save()
            else:
                self.post.like_count -= 1
                self.post.save()

            self.remove_upvote()

    def upvote_exists(self):
        return PostCommentLike.objects.filter(user=self.user, post=self.post,
                                              post_comment=self.post_comment, upvote=True).exists()

    def downvote_exists(self):
        return PostCommentLike.objects.filter(user=self.user, post=self.post,
                                              post_comment=self.post_comment, upvote=False).exists()

    def remove_upvote(self):
        PostCommentLike.objects.filter(user=self.user, post=self.post,
                                       post_comment=self.post_comment, upvote=True).delete()

    def remove_downvote(self):
        PostCommentLike.objects.filter(user=self.user, post=self.post,
                                       post_comment=self.post_comment, upvote=False).delete()

