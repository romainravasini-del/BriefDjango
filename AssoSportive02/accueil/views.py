"""
views.py : vues de l'application (la logique de chaque page).

Une vue reçoit une requête et renvoie une réponse (page HTML ou redirection).
Toutes les vues de ce projet sont des CLASSES (class-based views).

TYPES DE VUES UTILISÉS
  TemplateView   Affiche un gabarit. On ajoute des données via get_context_data().
  ListView       Affiche une liste d'objets (get_queryset() choisit lesquels).
  DetailView     Affiche un objet retrouvé par son identifiant (paramètre "pk").
  FormView       Affiche un formulaire, le valide, puis appelle form_valid().
  View           Vue de base : on écrit soi-même la méthode post() ou get().
                 Utilisée pour les actions qui MODIFIENT des données.

PROTECTION DES PAGES (côté serveur)
  LoginRequiredMixin    Un visiteur anonyme est redirigé vers la connexion.
  UserPassesTestMixin   Appelle test_func() : si elle renvoie False, un anonyme
                        est redirigé vers la connexion et un utilisateur connecté
                        reçoit une erreur 403. Sert ici à réserver les pages au coach.
  Un mixin se place AVANT la vue dans la liste d'héritage.

OUTILS DE L'ORM UTILISÉS
  select_related(...)   Récupère les objets liés dans la même requête SQL
                        (évite une requête par ligne affichée).
  filter(...)           Équivalent d'un WHERE ; des filter successifs se cumulent (AND).
  Q(...) | Q(...)       Condition OU ; Q(...) & Q(...) = ET.
  champ__gt / __gte / __lt / __icontains
                        Opérateurs : supérieur, supérieur ou égal, inférieur,
                        "contient" sans tenir compte de la casse.
  annotate(Count(...))  Ajoute une colonne calculée (GROUP BY). Ici : le nombre
                        d'inscrits de chaque séance, avec filter= pour ne compter
                        que l'état "inscrit".
  get_object_or_404     Renvoie l'objet ou une erreur 404 s'il n'existe pas.
  order_by("-champ")    Tri décroissant (le "-" inverse l'ordre).

AUTRES OUTILS
  messages              Messages affichés une fois dans la page suivante
                        (success, warning, error).
  redirect("nom")       Redirection vers une route par son nom. Après un POST, on
                        redirige toujours : un rechargement de la page ne
                        renvoie pas l'action une seconde fois.
  timezone              Dates et heures conscientes du fuseau horaire.

"""

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
    """
    Espace personnel : le contexte envoyé au gabarit dépend du rôle.

    Adhérent : séances à venir (avec recherche) et ses propres inscriptions à venir.
    Coach    : statistiques par état et inscriptions réparties jour / à venir / échues.
    """
    template_name = "accueil/espace_membre.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activites"] = Activite.objects.all()
        # Instant présent dans le fuseau du projet (et non en UTC)
        maintenant = timezone.localtime()

        # Séances À VENIR : un jour futur, OU aujourd'hui mais avec une heure de début
        seances = Seance.objects.select_related("activite", "coach").filter(
            Q(date__gt=maintenant.date()) |
            Q(date=maintenant.date(), heure_debut__gt=maintenant.time())
        ).order_by("date", "heure_debut")

        # Paramètres de recherche lus dans l'URL (méthode GET). .strip() retire les espaces
        recherche = self.request.GET.get("recherche", "").strip()
        activite_id = self.request.GET.get("activite", "").strip()
        date_debut = self.request.GET.get("date_debut", "").strip()
        heure_debut = self.request.GET.get("heure_debut", "").strip()

        # Chaque filtre n'est appliqué que s'il est renseigné ; les filtres se cumulent
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

        # Cette boucle évalue la requête et attache places_restantes à chaque séance.
        # Les objets restent dans le cache du queryset, donc le gabarit les retrouve.
        for seance in seances:
            seance.places_restantes = max(
                0, seance.places - seance.nombre_inscrits
            )

        # Inscriptions de l'adhérent connecté UNIQUEMENT (filtre sur request.user), limitées
        # aux séances à venir.
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
        # Données réservées au coach : l'adhérent ne reçoit jamais les statistiques
        if self.request.user.role == "gestionnaire":
            # Nombre d'inscriptions par état, pour les cartes et le graphique
            context["stats_etats"] = {
            "inscrit": Inscription.objects.filter(etat="inscrit").count(),
            "liste_attente": Inscription.objects.filter(etat="liste_attente").count(),
            "present": Inscription.objects.filter(etat="present").count(),
            "absent": Inscription.objects.filter(etat="absent").count(),
            "annule": Inscription.objects.filter(etat="annule").count(),
}
            aujourd_hui = timezone.localdate()
            # Toutes les inscriptions, de la plus récente à la plus ancienne
            toutes = Inscription.objects.select_related(
                "utilisateur", "seance", "seance__activite"
            ).order_by("-date_creation")
            # Filtre du coach : noms de paramètres distincts de ceux de l'adhérent
            activite_coach = self.request.GET.get("activite_coach", "").strip()
            date_coach = self.request.GET.get("date_coach", "").strip()
            if activite_coach:
                toutes = toutes.filter(seance__activite_id=activite_coach)
            if date_coach:
                toutes = toutes.filter(seance__date=date_coach)
            context["inscriptions_gestion"] = toutes
            # Les trois colonnes de l'espace coach : aujourd'hui, à venir, échues (passées)
            context["inscriptions_jour"] = toutes.filter(seance__date=aujourd_hui)
            context["inscriptions_avenir"] = toutes.filter(seance__date__gt=aujourd_hui)
            context["inscriptions_echues"] = toutes.filter(seance__date__lt=aujourd_hui)
        return context


class Accueil_view(TemplateView):
    """Page d'accueil publique : un simple gabarit, sans données particulières."""
    template_name = "accueil/accueil.html"


class Catalogue_view(ListView):
    """Catalogue public des séances, avec recherche par mot-clé et filtre par activité."""
    model = Seance
    template_name = "accueil/catalogue.html"
    # Nom de la liste dans le gabarit ({% for seance in seances %})
    context_object_name = "seances"

    def get_queryset(self):
        """Renvoie les séances filtrées, avec le nombre de places restantes."""
        seances = Seance.objects.select_related("activite", "coach").order_by("date", "heure_debut")
        recherche = self.request.GET.get("recherche", "").strip()
        activite_id = self.request.GET.get("activite", "").strip()

        # Le mot-clé est cherché dans plusieurs champs à la fois
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

        # Même principe que dans l'espace membre : la boucle évalue la requête et
        # place places_restantes sur chaque séance avant l'envoi au gabarit
        for seance in seances:
            seance.places_restantes = max(
                0, seance.places - seance.nombre_inscrits
            )

        return seances

    def get_context_data(self, **kwargs):
        """Ajoute la liste des activités et les valeurs saisies, pour réafficher le formulaire."""
        context = super().get_context_data(**kwargs)
        context["activites"] = Activite.objects.all()
        context["recherche"] = self.request.GET.get("recherche", "")
        context["activite_selectionnee"] = self.request.GET.get("activite", "")
        return context


class Seance_detail_view(DetailView):
    """Détail d'une séance : l'objet est retrouvé grâce au paramètre "pk" de l'adresse."""
    model = Seance
    template_name = "accueil/seance_detail.html"
    context_object_name = "seance"


class Connexion_view(FormView):
    """
    Page unique de connexion ET d'inscription (deux formulaires, une seule vue).

    Le bouton cliqué envoie action=connexion ou action=inscription : la vue en
    déduit le formulaire à traiter. Après succès, l'utilisateur est connecté
    et redirigé vers son espace.
    """
    template_name = "accueil/connexion.html"
    # reverse_lazy : l'adresse n'est calculée qu'à l'usage (urls.py n'est pas encore chargé ici)
    success_url = reverse_lazy("Espace_membre")

    def get_form_class(self):
        """Choisit le formulaire à traiter selon le bouton qui a envoyé la requête."""
        if self.request.method == "POST" and self.request.POST.get("action") == "inscription":
            return Formulaire_inscription
        return Formulaire_connexion

    def get_form_kwargs(self):
        """AuthenticationForm exige l'argument "request" ; le formulaire d'inscription non."""
        kwargs = super().get_form_kwargs()
        if self.get_form_class() is Formulaire_connexion:
            kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Fournit toujours les DEUX formulaires au gabarit.

        Le formulaire traité (avec ses erreurs éventuelles) garde ses données ;
        l'autre est recréé vide.
        """
        context = super().get_context_data(**kwargs)
        if isinstance(context["form"], Formulaire_inscription):
            context["inscription_form"] = context["form"]
            context["form"] = Formulaire_connexion()
        else:
            context["inscription_form"] = Formulaire_inscription()
        return context

    def form_valid(self, form):
        """Formulaire valide : crée le compte si inscription, puis ouvre la session."""
        if self.request.POST.get("action") == "inscription":
            # save() crée le compte (mot de passe haché, rôle "utilisateur" par défaut)
            user = form.save()
            login(self.request, user)
        else:
            login(self.request, form.get_user())
        # Redirige vers success_url
        return super().form_valid(form)


class Inscrire_seance_view(LoginRequiredMixin, View):
    """
    Inscrit l'adhérent connecté à une séance (POST uniquement).

    Pas de méthode get() : un accès par l'adresse seule (GET) est refusé par Django.
    Les règles métier sont vérifiées ici, côté serveur, jamais seulement dans le HTML.
    """
    def post(self, request, seance_id):
        # Règle : seuls les adhérents s'inscrivent (un coach ne le peut pas)
        if request.user.role != "utilisateur":
            messages.error(request, "Seuls les adhérents peuvent s'inscrire.")
            return redirect("Espace_membre")

        seance = get_object_or_404(Seance, pk=seance_id)

        debut = timezone.make_aware(
            datetime.combine(seance.date, seance.heure_debut),
            timezone.get_current_timezone()
        )

        # La séance stocke date et heure séparément : on les combine, puis on rend
        # l'instant "conscient" du fuseau horaire. Sans cela, Python refuse de comparer
        # cet instant à timezone.now()
        if debut <= timezone.now():
            messages.error(request, "Cette séance a déjà commencé.")
            return redirect("Espace_membre")

        # Règle : le certificat doit exister ET rester valable jusqu'à la date de la séance.
        if not request.user.certificat_jusqu_au or request.user.certificat_jusqu_au < seance.date:
            messages.error(request, "Votre certificat médical est absent ou expiré.")
            return redirect("Espace_membre")

        # Inscription déjà existante pour cet adhérent et cette séance.
        inscription = Inscription.objects.filter(
            utilisateur=request.user,
            seance=seance
        ).first()

        # Une inscription annulée peut être réactivée ; toute autre est un doublon.
        if inscription and inscription.etat != "annule":
            messages.warning(request, "Vous avez déjà une inscription pour cette séance.")
            return redirect("Espace_membre")

        # Seul l'état "inscrit" occupe une place.
        nombre_inscrits = Inscription.objects.filter(
            seance=seance,
            etat="inscrit"
        ).count()

        # Séance complète : liste d'attente au lieu d'un refus
        etat = "inscrit" if nombre_inscrits < seance.places else "liste_attente"

        # Réactive la ligne annulée, sinon en crée une nouvelle
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


class Annuler_inscription_view(LoginRequiredMixin, View):
    """Annule une inscription de l'adhérent connecté (POST uniquement)."""

    def post(self, request, inscription_id):
        """Vérifie la propriété, la date et l'état, puis annule et promeut la liste d'attente."""
        # utilisateur=request.user : un adhérent ne peut annuler que SES inscriptions.
        # Celle d'un autre renvoie une erreur 404 (contrôle de propriété côté serveur)
        inscription = get_object_or_404(
            Inscription,
            pk=inscription_id,
            utilisateur=request.user
        )

        # Début de la séance en date "consciente" (voir Inscrire_seance_view)
        debut = timezone.make_aware(
            datetime.combine(
                inscription.seance.date,
                inscription.seance.heure_debut
            ),
            timezone.get_current_timezone()
        )

        # Règle : on n'annule plus une séance commencée
        if debut <= timezone.now():
            messages.error(request, "Impossible d'annuler une séance déjà commencée.")

        # Seuls ces deux états sont annulables
        elif inscription.etat not in ["inscrit", "liste_attente"]:
            messages.error(request, "Cette inscription ne peut pas être annulée.")

        else:
            ancien_etat = inscription.etat
            inscription.etat = "annule"
            inscription.date_modification = timezone.now()
            inscription.save()
            # Une place se libère seulement si l'inscription annulée en occupait une
            if ancien_etat == "inscrit":
                # Premier de la liste d'attente = le plus ancien (tri par date de création)
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
    """Réserve une vue aux coachs : anonyme redirigé vers la connexion, adhérent en 403."""
    def test_func(self):
        """Renvoie True seulement si l'utilisateur est connecté ET a le rôle gestionnaire."""
        return (
            self.request.user.is_authenticated
            and self.request.user.role == "gestionnaire"
        )


class Gestion_view(GestionnaireRequiredMixin, ListView):
    """Espace du coach (/gestion/) : affiche le même gabarit que l'espace membre."""
    
    model = Inscription
    template_name = "accueil/espace_membre.html"
    context_object_name = "inscriptions_gestion"

    def get_queryset(self):
        """Toutes les inscriptions, de la plus récente à la plus ancienne."""
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
    """
    Changement d'état d'une inscription par le coach (POST uniquement).

    Toute transition absente de TRANSITIONS_AUTORISEES est refusée, même si la
    requête est forgée à la main : les boutons du gabarit ne sont qu'un confort.
    """
    # Table de règles : état actuel -> états autorisés. Un état absent de la table
    # (present, absent, annule) n'a plus aucune transition possible
    TRANSITIONS_AUTORISEES = {
        "inscrit": {"present", "absent", "annule"},
        "liste_attente": {"annule"},
    }

    def post(self, request, inscription_id):
        """Valide la transition demandée, l'applique, puis redirige vers la page d'origine."""

        inscription = get_object_or_404(Inscription, pk=inscription_id)
        # Valeur venant du champ caché du formulaire : modifiable par l'utilisateur,
        nouvel_etat = request.POST.get("etat", "")
        etats_permis = self.TRANSITIONS_AUTORISEES.get(inscription.etat, set())
        # "next" = nom de la route où revenir. Liste blanche : on ne redirige jamais
        # vers une valeur arbitraire fournie par le client
        next_url = request.POST.get("next", "gestion")
        if next_url not in {"gestion", "Espace_membre"}:
            next_url = "gestion"

        # Transition absente de la table : refus avec message
        if nouvel_etat not in etats_permis:
            messages.error(request, "Transition d'état non autorisée.")
            return redirect(next_url)

        ancien_etat = inscription.etat
        inscription.etat = nouvel_etat
        inscription.date_modification = timezone.now()
        inscription.save()

        # Annuler une inscription "inscrit" libère une place : le plus ancien de la
        # liste d'attente est promu (même logique que dans Annuler_inscription_view)
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



    


    
        
        
