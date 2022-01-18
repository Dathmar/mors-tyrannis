from django.contrib import admin
from .models import UserMeta


# Register your models here.
@admin.register(UserMeta)
class UserMetaAdmin(admin.ModelAdmin):
    list_display = ('user', 'reputation')
    list_editable = ('reputation',)
    search_fields = ('user',)
    list_filter = ('reputation',)
