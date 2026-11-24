from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView, ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import Formulaire_inscription, Formulaire_connexion
from .models import Seance, Inscription, Activite


class Espace_membre_view(LoginRequiredMixin,TemplateView):
    template_name = "accueil/espace_membre.html"


    def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["activites"] = Activite.objects.all()
                seances = Seance.objects.select_related("activite", "coach").order_by("date", "heure_debut")
                recherche = self.request.GET.get("recherche", "").strip()
                activite_id = self.request.GET.get ("activite", "").strip()
                if recherche:
                    seances = seances.filter(Q(activite__nom__icontains=recherche)|Q(lieu__icontains=recherche)|Q(description__icontains=recherche))
                if activite_id:
                    seances = seances.filter(activite_id=activite_id)
                context["seances"] = seances
                context["activite_selectionnee"]=activite_id
                context["inscriptions"] = Inscription.objects.filter(utilisateur=self.request.user)
                context["recherche"] = self.request.GET.get("recherche", "")
                return context

class Accueil_view(TemplateView):
    template_name = "accueil/accueil.html"

class Catalogue_view(ListView):
    model = Seance
    template_name = "accueil/catalogue.html"
    context_object_name = "seances"

    def get_queryset(self):
        seances = Seance.objects.select_related("activite", "coach").order_by("date", "heure_debut")
        recherche = self.request.GET.get("recherche", "").strip()
        activite_id = self.request.GET.get ("activite", "").strip()
        if recherche:
            seances = seances.filter(Q(activite__nom__icontains=recherche)|Q(lieu__icontains=recherche)|Q(description__icontains=recherche))
        if activite_id:
            seances = seances.filter(activite_id=activite_id)
        return seances
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context["activites"] = Activite.objects.all()
        context["recherche"] = self.request.GET.get("recherche", "")
        context["activite_selectionnee"]=self.request.GET.get("activite","")
        return context

class Seance_detail_view(DetailView):
    model = Seance
    template_name = "accueil/seance_detail.html"
    context_object_name = "seance"

class Connexion_view(FormView):
    template_name = "accueil/connexion.html"
    success_url = reverse_lazy("Espace_membre")

    def get_form_class(self):
        if self.request.method == "POST" and self.request.POST.get("action") == "inscription":
            return Formulaire_inscription
        return Formulaire_connexion

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() is Formulaire_connexion:
            kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if isinstance(context["form"], Formulaire_inscription):
            context["inscription_form"] = context["form"]
            context["form"] = Formulaire_connexion()
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

