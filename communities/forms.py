from django import forms
from django_markdown.widgets import MarkdownWidget


class CommentForm(forms.Form):
    content = forms.CharField(widget=MarkdownWidget())


class CommunityForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=MarkdownWidget())
    is_public = forms.BooleanField(required=False)


class PostForm(forms.Form):
    content = forms.CharField(widget=MarkdownWidget())

