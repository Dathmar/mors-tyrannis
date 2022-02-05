from django.shortcuts import render
from django.db.models import Q
from django.views import View

from communities.models import PostComment
from .models import UserMeta
from datetime import datetime


# Create your views here.
def index(request):
    return render(request, 'users/index.html')


class NotificationCenterView(View):
    def get(self, request):
        user_meta = UserMeta.objects.get(user=request.user)
        post_comments = PostComment.objects.filter(((Q(post__user=request.user) & Q(postcomment=None))
                                                    | Q(postcomment__user=request.user))
                                                   & Q(created_at__gt=user_meta.last_notification_check))
        user_meta.last_notification_check = datetime.utcnow()
        user_meta.save()
        return render(request, 'users/notification-center.html', {'post_comments': post_comments})