from django import forms
from .models import Post, Community


class CommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, required=True)


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'is_private', 'require_join_approval']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_join_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        reserved_community_names = ['create', ]

        if self.cleaned_data['name'] in reserved_community_names:
            raise forms.ValidationError('This name is reserved.')
        return self.cleaned_data['name']


class TextPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'nsfw_flag']
        widgets = {
            'post_type': forms.Select(attrs={'onchange': 'change_post_type(this)'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Content'}),
            'nsfw_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        if not self.cleaned_data['title']:
            raise forms.ValidationError('Title is required.')
        return self.cleaned_data['title']

    def clean_content(self):
        if not self.cleaned_data['content']:
            raise forms.ValidationError('Content is required.')
        return self.cleaned_data['content']


class ImagePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'image', 'nsfw_flag']
        widgets = {
            'post_type': forms.Select(attrs={'onchange': 'change_post_type(this)'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'image': forms.FileInput(),
            'nsfw_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        if not self.cleaned_data['title']:
            raise forms.ValidationError('Title is required.')
        return self.cleaned_data['title']

    def clean_image(self):
        if not self.cleaned_data['image']:
            raise forms.ValidationError('Image is required.')
        return self.cleaned_data['image']


class LinkPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'url', 'nsfw_flag']
        widgets = {
            'post_type': forms.Select(attrs={'onchange': 'change_post_type(this)'}, choices=Post.post_types),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Content'}),
            'nsfw_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        if not self.cleaned_data['title']:
            raise forms.ValidationError('Title is required.')
        return self.cleaned_data['title']

    def clean_url(self):
        if not self.cleaned_data['url']:
            raise forms.ValidationError('URL is required.')
        return self.cleaned_data['url']

