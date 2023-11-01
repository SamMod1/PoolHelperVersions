from django.shortcuts import get_object_or_404, render, redirect

def home(request):
    return redirect('portal/')
