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

     path("activite/", 
     views.Seance_detail_view.as_view(), 
     name="seance_detail"),

]