"""
urls.py : table des adresses (routes) de l'application "accueil".

Une route relie une ADRESSE à une VUE :
    path("adresse/", vue, name="nom")

OPTIONS UTILISÉES
  - Premier argument : l'adresse, sans le domaine ni le "/" initial.
    "" désigne la racine du site.
  - Deuxième argument : la vue. Les vues sont des classes, donc on appelle
    .as_view() pour obtenir la fonction que Django attend.
  - name="..." : nom de la route. C'est ce nom, et non l'adresse, qu'on utilise
    dans les gabarits ({% url 'nom' %}) et dans les vues (redirect("nom")).
    On peut ainsi changer une adresse sans modifier le reste du code.
    Les noms sont sensibles à la casse (ex. "Espace_membre").
  - <int:pk> et <int:seance_id> : paramètre dans l'adresse. "int" n'accepte que
    des nombres ; la valeur est transmise à la vue sous le nom indiqué. Ce nom
    doit être identique à celui attendu par la vue (DetailView attend "pk" ;
    les vues View de ce projet attendent "seance_id" ou "inscription_id").

ROUTES DU PROJET
  /                                       Accueil (public)
  /connexion/  et  /inscription/          Connexion + inscription (même page)
  /deconnexion/                           Déconnexion (POST uniquement)
  /espace_membre/                         Espace adhérent ou coach (connecté)
  /catalogue/ et /catalogue/<pk>/         Liste et détail des séances
  /seance/<id>/inscrire/                  Inscription à une séance (POST)
  /inscription/<id>/annuler/              Annulation d'une inscription (POST)
  /gestion/                               Espace du coach (gestionnaire)
  /gestion/<id>/changer-etat/             Changement d'état (POST, coach)
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
     # Page d'accueil publique
     path("",
          views.Accueil_view.as_view(),
          name="accueil"),

     # Page de connexion (contient aussi le formulaire d'inscription)
     path("connexion/",
          views.Connexion_view.as_view(),
          name="connexion"),

     # Vue fournie par Django : next_page indique le NOM de la route où aller après
     # la déconnexion. Elle n'accepte que le POST (d'où le formulaire dans les gabarits)
     path("deconnexion/",
          auth_views.LogoutView.as_view(next_page="connexion"),
          name="deconnexion"),

     path("espace_membre/",
          views.Espace_membre_view.as_view(),
          name="Espace_membre"),

     # Adresse imposée par le brief : elle réutilise la vue de connexion, qui affiche
     # les deux formulaires et choisit lequel traiter selon le bouton cliqué
     path("inscription/",
          views.Connexion_view.as_view(),
          name="inscription"),

     path("catalogue/",
          views.Catalogue_view.as_view(),
          name="catalogue"),

     # <int:pk> : une DetailView retrouve la séance grâce à ce paramètre nommé "pk"
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
