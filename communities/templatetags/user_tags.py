from django import template
from communities.models import CommunityMember

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
