"""
apps.py : configuration de l'application Django "accueil".

Django lit ce fichier au démarrage pour connaître les applications installées
(liste INSTALLED_APPS de settings.py). L'attribut `name` doit correspondre
exactement au nom du dossier de l'application.
"""
from django.apps import AppConfig

class AccueilConfig(AppConfig):
    """Configuration de l'application "accueil" (modèles, vues et gabarits du site)."""
    name = 'accueil'
