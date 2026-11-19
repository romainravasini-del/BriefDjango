from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def accueil(request):
    if request.user.is_authenticated:
        return redirect("Espace_membre")
    else:
        return redirect("connexion")


@login_required
def Espace_membre(request):
    return HttpResponse("Vous voici dans votre espaces membre.")

# Create your views here.
