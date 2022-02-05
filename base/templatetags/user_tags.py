from django import template
from django.db.models import Q
from communities.models import CommunityMember, PostComment
from users.models import UserMeta

register = template.Library()


@register.simple_tag
def is_community_member(community, user):
    if user.is_authenticated:
        if CommunityMember.objects.filter(community=community, user=user).exists():
            return True
    return False


@register.filter(name='has_user_upvote')
def has_user_upvote(obj, user):
    return obj.has_user_upvote(user)


@register.filter(name='has_user_downvote')
def has_user_downvote(obj, user):
    return obj.has_user_downvote(user)


@register.filter(name='user_has_notification')
def user_has_notification(user):
    if user.is_authenticated:
        user_meta = UserMeta.objects.get(user=user)
        return PostComment.objects.filter(((Q(post__user=user) & Q(postcomment=None))
                                           | Q(postcomment__user=user))
                                          & Q(created_at__gt=user_meta.last_notification_check)).exists()
    return False