from django import forms


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


class PostForm(forms.Form):
    post_type = forms.ChoiceField(choices=((0, 'text'), (1, 'image'), (2, 'link')), required=True)
    title = forms.CharField(max_length=3000, required=True)
    content = forms.CharField(widget=forms.Textarea, required=True)
    nsfw_flag = forms.BooleanField(required=False)
