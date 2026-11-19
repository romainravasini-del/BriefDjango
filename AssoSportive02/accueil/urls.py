from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path("", views.Accueil_view.as_view(), name="accueil"),

    path("connexion/", 
         auth_views.LoginView.as_view(
            template_name="accueil/connexion.html"
         ),
         name="connexion"
         ),

    path("deconnexion/", 
         auth_views.LogoutView.as_view(next_page="connexion"),
         name="deconnexion"
         ),

    path("espace_membre/", 
         views.Espace_membre_view.as_view(),
         name="Espace_membre"
         ),
]