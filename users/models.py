from django.db import models
from django.conf import settings


# Create your models here.
class UserMeta(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reputation = models.IntegerField(default=0)
    last_notification_check = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def add_reputation(self, rep):
        self.reputation += rep
        self.save()
