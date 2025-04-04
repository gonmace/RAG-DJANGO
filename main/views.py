from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    if not request.user.is_superuser:
        return redirect('main:panel')  # o mostrar un template con mensaje
    return render(request, 'home_page.html')

@login_required
def panel(request):
    return render(request, 'panel.html')