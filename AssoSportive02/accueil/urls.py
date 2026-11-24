
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path("",
         views.Accueil_view.as_view(),
         name="accueil"),

    path("connexion/",
         views.Connexion_view.as_view(),
         name="connexion"),

    path("deconnexion/",
         auth_views.LogoutView.as_view(next_page="connexion"),
         name="deconnexion"),

    path("espace_membre/",
         views.Espace_membre_view.as_view(),
         name="Espace_membre"),

    path("inscription/",
         views.Connexion_view.as_view(),
         name="inscription"),

    path("catalogue/",
         views.Catalogue_view.as_view(),
         name="catalogue"),

    path("catalogue/<int:pk>/",
         views.Seance_detail_view.as_view(),
         name="seance_detail"),

    # AJOUT 1 : inscription à une séance
    path("seance/<int:seance_id>/inscrire/",
         views.Inscrire_seance_view.as_view(),
         name="inscrire_seance"),

    # AJOUT 2 : annulation d'une inscription
    path("inscription/<int:inscription_id>/annuler/",
         views.Annuler_inscription_view.as_view(),
         name="annuler_inscription"),

    path("gestion/",
         views.Gestion_view.as_view(),
         name="gestion"),

    path("gestion/<int:inscription_id>/changer-etat/",
         views.Gestion_transition_view.as_view(),
         name="gestion_changer_etat"),

]
