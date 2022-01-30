from django import template
from communities.models import CommunityMember

register = template.Library()


@register.simple_tag
def is_community_member(community, user):
    if user.is_authenticated:
        if CommunityMember.objects.filter(community=community, user=user).exists():
            return True
    return False
