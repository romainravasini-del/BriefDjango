
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, FormView, ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .forms import Formulaire_inscription, Formulaire_connexion
from .models import Seance, Inscription, Activite
# imports pour les inscriptions aux séances
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime


class Espace_membre_view(LoginRequiredMixin, TemplateView):
    template_name = "accueil/espace_membre.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activites"] = Activite.objects.all()
        maintenant = timezone.localtime()

        seances = Seance.objects.select_related("activite", "coach").filter(
            Q(date__gt=maintenant.date()) |
            Q(date=maintenant.date(), heure_debut__gt=maintenant.time())
        ).order_by("date", "heure_debut")

        

        recherche = self.request.GET.get("recherche", "").strip()
        activite_id = self.request.GET.get("activite", "").strip()
        date_debut = self.request.GET.get("date_debut", "").strip()
        heure_debut = self.request.GET.get("heure_debut", "").strip()

        if recherche:
            seances = seances.filter(Q(activite__nom__icontains=recherche)|Q(lieu__icontains=recherche)|Q(description__icontains=recherche)|Q(date__contains=recherche)|Q(heure_debut__contains=recherche))

        if activite_id:
            seances = seances.filter(activite_id=activite_id)

        if date_debut:
            seances = seances.filter(date__gte=date_debut)

        if heure_debut:
            seances = seances.filter(heure_debut__gte=heure_debut)

        # AJOUT : calcul des places occupées et restantes
        seances = seances.annotate(
            nombre_inscrits=Count(
                "inscription",
                filter=Q(inscription__etat="inscrit")
            )
        )

        for seance in seances:
            seance.places_restantes = max(
                0, seance.places - seance.nombre_inscrits
            )

        context["seances"] = seances
        context["activite_selectionnee"] = activite_id
        context["inscriptions"] = Inscription.objects.filter(
            utilisateur=self.request.user
        ).filter(
            Q(seance__date__gt=maintenant.date()) |
            Q(
                seance__date=maintenant.date(),
                seance__heure_debut__gt=maintenant.time()
            )
        ).select_related("seance", "seance__activite").order_by(
            "seance__date", "seance__heure_debut"
        )
        context["recherche"] = self.request.GET.get("recherche", "")
        if self.request.user.role == "gestionnaire":
            context["stats_etats"] = {
            "inscrit": Inscription.objects.filter(etat="inscrit").count(),
            "liste_attente": Inscription.objects.filter(etat="liste_attente").count(),
            "present": Inscription.objects.filter(etat="present").count(),
            "absent": Inscription.objects.filter(etat="absent").count(),
            "annule": Inscription.objects.filter(etat="annule").count(),
}
            aujourd_hui = timezone.localdate()
            toutes = Inscription.objects.select_related(
                "utilisateur", "seance", "seance__activite"
            ).order_by("-date_creation")
            activite_coach = self.request.GET.get("activite_coach", "").strip()
            date_coach = self.request.GET.get("date_coach", "").strip()
            if activite_coach:
                toutes = toutes.filter(seance__activite_id=activite_coach)
            if date_coach:
                toutes = toutes.filter(seance__date=date_coach)
            context["inscriptions_gestion"] = toutes
            context["inscriptions_jour"] = toutes.filter(seance__date=aujourd_hui)
            context["inscriptions_avenir"] = toutes.filter(seance__date__gt=aujourd_hui)
            context["inscriptions_echues"] = toutes.filter(seance__date__lt=aujourd_hui)
        return context

        date_debut = self.request.GET.get("date_debut", "").strip()
        heure_debut = self.request.GET.get("heure_debut", "").strip()
        if date_debut:
            seances = seances.filter(date__gte=date_debut)
        if heure_debut:
            seances = seances.filter(heure_debut__gte=heure_debut)


class Accueil_view(TemplateView):
    template_name = "accueil/accueil.html"


class Catalogue_view(ListView):
    model = Seance
    template_name = "accueil/catalogue.html"
    context_object_name = "seances"

    def get_queryset(self):
        seances = Seance.objects.select_related("activite", "coach").order_by("date", "heure_debut")
        recherche = self.request.GET.get("recherche", "").strip()
        activite_id = self.request.GET.get("activite", "").strip()

        if recherche:
            seances = seances.filter(Q(activite__nom__icontains=recherche)|Q(lieu__icontains=recherche)|Q(description__icontains=recherche))

        if activite_id:
            seances = seances.filter(activite_id=activite_id)

        # AJOUT : calcul des places occupées et restantes
        seances = seances.annotate(
            nombre_inscrits=Count(
                "inscription",
                filter=Q(inscription__etat="inscrit")
            )
        )

        for seance in seances:
            seance.places_restantes = max(
                0, seance.places - seance.nombre_inscrits
            )

        return seances

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activites"] = Activite.objects.all()
        context["recherche"] = self.request.GET.get("recherche", "")
        context["activite_selectionnee"] = self.request.GET.get("activite", "")
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


# permettre à un adhérent de s'inscrire à une séance
class Inscrire_seance_view(LoginRequiredMixin, View):

    def post(self, request, seance_id):
        if request.user.role != "utilisateur":
            messages.error(request, "Seuls les adhérents peuvent s'inscrire.")
            return redirect("Espace_membre")

        seance = get_object_or_404(Seance, pk=seance_id)

        debut = timezone.make_aware(
            datetime.combine(seance.date, seance.heure_debut),
            timezone.get_current_timezone()
        )

        if debut <= timezone.now():
            messages.error(request, "Cette séance a déjà commencé.")
            return redirect("Espace_membre")

        if not request.user.certificat_jusqu_au or request.user.certificat_jusqu_au < seance.date:
            messages.error(request, "Votre certificat médical est absent ou expiré.")
            return redirect("Espace_membre")

        inscription = Inscription.objects.filter(
            utilisateur=request.user,
            seance=seance
        ).first()

        if inscription and inscription.etat != "annule":
            messages.warning(request, "Vous avez déjà une inscription pour cette séance.")
            return redirect("Espace_membre")

        nombre_inscrits = Inscription.objects.filter(
            seance=seance,
            etat="inscrit"
        ).count()

        etat = "inscrit" if nombre_inscrits < seance.places else "liste_attente"

        if inscription:
            inscription.etat = etat
            inscription.save()
        else:
            Inscription.objects.create(
                utilisateur=request.user,
                seance=seance,
                etat=etat
            )

        messages.success(request, "Votre demande a été enregistrée.")
        return redirect("Espace_membre")


# permettre à un adhérent d'annuler sa participation
class Annuler_inscription_view(LoginRequiredMixin, View):

    def post(self, request, inscription_id):
        inscription = get_object_or_404(
            Inscription,
            pk=inscription_id,
            utilisateur=request.user
        )

        debut = timezone.make_aware(
            datetime.combine(
                inscription.seance.date,
                inscription.seance.heure_debut
            ),
            timezone.get_current_timezone()
        )

        if debut <= timezone.now():
            messages.error(request, "Impossible d'annuler une séance déjà commencée.")

        elif inscription.etat not in ["inscrit", "liste_attente"]:
            messages.error(request, "Cette inscription ne peut pas être annulée.")

        else:
            ancien_etat = inscription.etat
            inscription.etat = "annule"
            inscription.date_modification = timezone.now()
            inscription.save()
            if ancien_etat == "inscrit":
                prochain = (
                    Inscription.objects.filter(
                        seance=inscription.seance,
                        etat="liste_attente",
                    )
                    .order_by("date_creation")
                    .first()
                )
                if prochain:
                    prochain.etat = "inscrit"
                    prochain.date_modification = timezone.now()
                    prochain.save()
            messages.success(request, "Votre participation a été annulée.")

        return redirect("Espace_membre")

class GestionnaireRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == "gestionnaire"
        )


class Gestion_view(GestionnaireRequiredMixin, ListView):
    
    model = Inscription
    template_name = "accueil/espace_membre.html"
    context_object_name = "inscriptions_gestion"

    def get_queryset(self):
        return Inscription.objects.select_related(
            "utilisateur", "seance", "seance__activite"
        ).order_by("-date_creation")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aujourd_hui = timezone.localdate()
        toutes = context["inscriptions_gestion"]
        activite_coach = self.request.GET.get("activite_coach", "").strip()
        date_coach = self.request.GET.get("date_coach", "").strip()
        if activite_coach:
            toutes = toutes.filter(seance__activite_id=activite_coach)
        if date_coach:
            toutes = toutes.filter(seance__date=date_coach)
        context["activites"] = Activite.objects.all()
        context["inscriptions_jour"] = toutes.filter(seance__date=aujourd_hui)
        context["inscriptions_avenir"] = toutes.filter(seance__date__gt=aujourd_hui)
        context["inscriptions_echues"] = toutes.filter(seance__date__lt=aujourd_hui)
        context["stats_etats"] = {
            "inscrit": Inscription.objects.filter(etat="inscrit").count(),
            "liste_attente": Inscription.objects.filter(etat="liste_attente").count(),
            "present": Inscription.objects.filter(etat="present").count(),
            "absent": Inscription.objects.filter(etat="absent").count(),
            "annule": Inscription.objects.filter(etat="annule").count(),
        }
        return context

class Gestion_transition_view(GestionnaireRequiredMixin, View):
    TRANSITIONS_AUTORISEES = {
        "inscrit": {"present", "absent", "annule"},
        "liste_attente": {"annule"},
    }

    def post(self, request, inscription_id):
        inscription = get_object_or_404(Inscription, pk=inscription_id)
        nouvel_etat = request.POST.get("etat", "")
        etats_permis = self.TRANSITIONS_AUTORISEES.get(inscription.etat, set())
        next_url = request.POST.get("next", "gestion")
        if next_url not in {"gestion", "Espace_membre"}:
            next_url = "gestion"

        if nouvel_etat not in etats_permis:
            messages.error(request, "Transition d'état non autorisée.")
            return redirect(next_url)

        ancien_etat = inscription.etat
        inscription.etat = nouvel_etat
        inscription.date_modification = timezone.now()
        inscription.save()

        if ancien_etat == "inscrit" and nouvel_etat == "annule":
            prochain = (
                Inscription.objects.filter(
                    seance=inscription.seance,
                    etat="liste_attente",
                )
                .order_by("date_creation")
                .first()
            )
            if prochain:
                prochain.etat = "inscrit"
                prochain.date_modification = timezone.now()
                prochain.save()

        messages.success(request, f"Inscription passée à « {inscription.get_etat_display()} ».")
        return redirect(next_url)



    


    
        
        
