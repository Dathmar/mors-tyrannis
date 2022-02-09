# accounts/views.py
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import SignUpForm
from users.models import UserMeta
from communities.models import Community, CommunityMember


class SignUpView(generic.CreateView):
    #  https://simpleisbetterthancomplex.com/tutorial/2017/02/18/how-to-create-user-sign-up-view.html
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            user_meta = UserMeta.objects.create(user=user)
            user_meta.save()

            auto_follow_communities(user)

            login(request, user)
            return redirect(self.success_url)


def auto_follow_communities(user):
    auto_communities = Community.objects.filter(auto_follow=True)
    for community in auto_communities:
        cm = CommunityMember.objects.create(
            user=user,
            community=community,
            following=True
        )
        cm.save()
