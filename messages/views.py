from django.shortcuts import render
from .models import DirectMessage
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url='/accounts/login/?next=/m/')
def index(request):
    messages = DirectMessage.objects.filter(receiver=request.user).values('sender').distinct()
    return render(request, 'messages/index.html', {'messages': messages})


