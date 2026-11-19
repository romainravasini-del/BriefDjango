from django.shortcuts import redirect
#from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class Espace_membre_view(LoginRequiredMixin,TemplateView):
    template_name = "accueil/espace_membre.html"

# def accueil(request):
#     if request.user.is_authenticated:
#         return redirect("Espace_membre")
#     else:
#         return redirect("connexion")

class Accueil_view(TemplateView):
    template_name = "accueil/accueil.html"

# Create your views here.
