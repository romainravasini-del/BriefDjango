from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import Formulaire_inscription

class Espace_membre_view(LoginRequiredMixin,TemplateView):
    template_name = "accueil/espace_membre.html"

class Accueil_view(TemplateView):
    template_name = "accueil/accueil.html"

class Connexion_view(FormView):
    template_name = "accueil/connexion.html"
    success_url = reverse_lazy("Espace_membre")

    def get_form_class(self):
        if self.request.method == "POST" and self.request.POST.get("action") == "inscription":
            return Formulaire_inscription
        return AuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() is AuthenticationForm:
            kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if isinstance(context["form"], Formulaire_inscription):
            context["inscription_form"] = context["form"]
            context["form"] = AuthenticationForm()
        else:
            context["inscription_form"] = Formulaire_inscription()
        return context

    def form_valid(self, form):
        if self.request.POST.get("action") == "inscription":
            user = form.save()
            login(self.request, user)
        else:
            login(self.request, form.get_user())
        return super().form_valid(form)
# Create your views here.

