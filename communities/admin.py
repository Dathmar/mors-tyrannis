from django.contrib import admin
from .models import Post, PostCommentLike, CommunityMember


# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'dislike_count', 'like_count')
    list_editable = ('dislike_count', 'like_count')
    list_filter = ('title', 'community')
    search_fields = ('title', 'community')


@admin.register(PostCommentLike)
class PostCommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'post_comment', 'upvote')
    list_filter = ('user', 'post', 'post_comment', 'upvote')
    search_fields = ('user', 'post', 'post_comment', 'upvote')
    list_editable = ('post', 'post_comment', 'upvote')


@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'community_rep')
    list_filter = ('user', 'community')
    search_fields = ('user', 'community')
    list_editable = ('community', 'community_rep')

