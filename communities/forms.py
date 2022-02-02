from django import forms
from .models import Post


class CommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, required=True)


class CommunityForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'size-form-textarea', 'placeholder': 'Community description',
                                     'rows': '2', 'style': 'width:100%;'}), required=True)
    is_private = forms.BooleanField(required=False)
    require_join_approval = forms.BooleanField(required=False)

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
