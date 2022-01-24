from communities.models import PostCommentLike, CommunityMember
from users.models import UserMeta
import logging

logger = logging.getLogger('app_api')


def toggle_upvote(user, post, post_comment=None):
    obj = post_comment or post
    rep_change = 0
    if remove_downvote_if_exists(user=user, post=post, post_comment=post_comment):
        rep_change += 1
        obj.dislike_count -= 1

    if remove_upvote_if_exists(user=user, post=post, post_comment=post_comment):
        rep_change -= 1
        obj.like_count -= 1
    else:
        rep_change += 1
        obj.like_count += 1
        add_upvote(user=user, post=post, post_comment=post_comment)

    add_user_rep(rep_change, post, post_comment)
    obj.save()


def toggle_downvote(user, post, post_comment=None):
    obj = post_comment or post
    rep_change = 0
    if remove_upvote_if_exists(user=user, post=post, post_comment=post_comment):
        rep_change -= 1
        obj.like_count -= 1

    if remove_downvote_if_exists(user=user, post=post, post_comment=post_comment):
        rep_change += 1
        obj.dislike_count -= 1
    else:
        rep_change -= 1
        obj.dislike_count += 1
        add_downvote(user=user, post=post, post_comment=post_comment)

    add_user_rep(rep_change, post, post_comment)
    obj.save()


def add_upvote(user, post, post_comment=None):
    post_comment_like = PostCommentLike.objects.create(
        user=user,
        upvote=True,
        post=post,
        post_comment=post_comment
    )
    post_comment_like.save()


def add_downvote(user, post, post_comment=None):
    post_comment_like = PostCommentLike.objects.create(
        user=user,
        upvote=False,
        post=post,
        post_comment=post_comment
    )
    post_comment_like.save()


def remove_upvote_if_exists(user, post, post_comment=None):
    if post_comment:
        pcl = PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=True)
    else:
        pcl = PostCommentLike.objects.filter(user=user, post=post, upvote=True)

    if pcl.exists():
        pcl.first().delete()
        return True

    return False


def remove_downvote_if_exists(user, post, post_comment=None):
    if post_comment:
        pcl = PostCommentLike.objects.filter(user=user, post=post, post_comment=post_comment, upvote=False)
    else:
        pcl = PostCommentLike.objects.filter(user=user, post=post, upvote=False)

    if pcl.exists():
        pcl.first().delete()
        return True

    return False


def add_user_rep(rep_val, post, post_comment=None):
    if post_comment:
        community = post_comment.community
        user = post_comment.user
    else:
        community = post.community
        user = post.user

    community_member = CommunityMember.objects.get(community=community, user=user)
    user_meta = UserMeta.objects.get(user=user)
    community_member.add_community_rep(rep_val)
    user_meta.add_reputation(rep_val)


def create_voting(user, post, post_comment=None):
    if post_comment:
        obj = post_comment
    else:
        obj = post

    add_user_rep(rep_val=1, post=post, post_comment=post_comment)
    add_upvote(user=user, post=post, post_comment=post_comment)
    obj.like_count += 1
    obj.save()

