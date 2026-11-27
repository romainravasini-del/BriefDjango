# Import des outils d'administration de Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin    

# Import des modèles de l'application
from accueil.models import Utilisateur, Inscription, Activite, Seance

# Ajout des modèles dans l'administration Django
admin.site.register(Utilisateur,UserAdmin)
admin.site.register(Inscription)
admin.site.register(Activite)
admin.site.register(Seance)