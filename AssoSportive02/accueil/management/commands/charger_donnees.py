"""
charger_donnees.py : commande Django qui remplit la base à partir des CSV de data/.

Lancement : python manage.py charger_donnees
(le nom de la commande est le nom du fichier, qui doit se trouver dans
accueil/management/commands/, avec un __init__.py dans management/ et commands/).

CE QUE FAIT LA COMMANDE, DANS L'ORDRE
  1. utilisateurs.csv -> table Utilisateur (mot de passe haché)
  2. categories.csv   -> table Activite
  3. objets.csv       -> table Seance
  4. actions.csv      -> table Inscription
  L'ordre suit les dépendances : une séance référence une activité et un coach
  (un utilisateur), une inscription référence un utilisateur et une séance.
  Un fichier est donc toujours chargé APRÈS ceux auxquels il fait référence.

OPTIONS ET OUTILS UTILISÉS
  BaseCommand           Classe de base d'une commande. Django exécute sa
                        méthode handle() ; l'attribut help s'affiche avec
                        `python manage.py help charger_donnees`.
  csv.DictReader        Lit chaque ligne du CSV comme un dictionnaire
                        {nom_colonne: valeur}. Toutes les valeurs sont des
                        chaînes : il faut convertir (int, dates).
  open(..., encoding="utf-8", newline="")
                        utf-8 pour les accents ; newline="" est recommandé par la
                        documentation du module csv.
  Path et l'opérateur /   settings.BASE_DIR est le dossier de manage.py ;
                        .parent remonte d'un niveau (vers la racine du dépôt) ;
                        "/" ajoute un sous-dossier ou un fichier au chemin.
  update_or_create(clé, defaults={...})
                        Cherche une ligne avec la clé donnée : si elle existe,
                        elle est MISE À JOUR avec defaults, sinon elle est CRÉÉE.
                        Renvoie (objet, créé?). C'est ce qui rend la commande
                        RELANÇABLE SANS DOUBLON.
  parse_date / parse_datetime
                        Convertissent un texte ISO en date / date-heure Python.
  timezone.make_aware   Rend une date-heure "consciente" du fuseau horaire. Sans
                        cela, Django avertit (naive datetime) car USE_TZ est actif.

CORRESPONDANCE DES IDENTIFIANTS (point de vigilance du brief)
  Les id du CSV ne sont pas ceux de la base pour les comptes (Django les numérote
  lui-même). Le dictionnaire `utilisateurs` garde donc le lien
  {id dans le CSV: objet Utilisateur en base}, utilisé ensuite pour relier
  séances (coach) et inscriptions (adhérent) au bon compte.
  Les activités, séances et inscriptions réutilisent directement l'id du CSV.

DATES CONSERVÉES
  date_creation et date_modification viennent du fichier. Cela fonctionne parce
  que les champs du modèle utilisent default=timezone.now (modifiable) et non
  auto_now_add (qui écraserait la valeur du CSV).
"""

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime,parse_date
from django.utils import timezone
from accueil.models import Activite, Utilisateur, Seance, Inscription 

import datetime


class Command(BaseCommand):
    """Commande de chargement : lit les quatre CSV et remplit les tables correspondantes."""

    # Description affichée par `python manage.py help charger_donnees`
    help = "Charge les données CSV dans la base"

    def handle(self, *args, **options):
        """Point d'entrée exécuté par Django : charge les fichiers dans l'ordre des dépendances."""
        # Dossier data/ à la racine du dépôt. Calculé depuis BASE_DIR : le chemin ne
        # dépend pas de l'endroit où la commande est lancée
        file = settings.BASE_DIR.parent / "data" 

        # Table de correspondance {id CSV: Utilisateur}, remplie ici et réutilisée plus bas
        utilisateurs = {}

        # ---------- 1. Comptes (en premier : séances et inscriptions en dépendent) ----------
        with open(file / "utilisateurs.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                # Clé de recherche = l'e-mail (unique). Relancer la commande met à jour
                # le compte existant au lieu d'en créer un second
                utilisateur, cree = Utilisateur.objects.update_or_create(
                    email=ligne["email"],
                    defaults={
                        # L'e-mail sert d'identifiant de connexion (consigne du brief)
                        "username": ligne["email"],
                        "first_name": ligne["prenom"],
                        "last_name": ligne["nom"],
                        "email": ligne["email"],
                        "role": ligne["role"],
                        # Certificat facultatif : une colonne vide devient NULL (None) en base
                        "certificat_jusqu_au": parse_date(ligne["certificat_valide_jusqu_au"]) if ligne["certificat_valide_jusqu_au"].strip() else None,
                    },
                )
                # set_password HACHE le mot de passe : il n'est jamais stocké en clair.
                # Tous les comptes de démonstration ont demo1234
                utilisateur.set_password("demo1234")
                utilisateur.save()
                # On mémorise le lien id du CSV -> compte réel pour les fichiers suivants
                utilisateurs[ligne["id"]] = utilisateur
                print(utilisateur, "créée" if cree else "mise à jour")

        # ---------- 2. Activités (le fichier s'appelle categories.csv) ----------
        with open(file / "categories.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                # On réutilise l'id du CSV comme clé : les séances y font référence
                activite, cree = Activite.objects.update_or_create(
                    id=int(ligne["id"]),
                    defaults={"nom"                 :ligne["nom"]},
                )
                print(activite, "créée" if cree else "mise à jour")
            print()

        # ---------- 3. Séances (nécessitent les activités et les coachs) ----------
        with open(file / "objets.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                seance, cree = Seance.objects.update_or_create(
                    id=int(ligne["id"]),
                    # "activite_id" : on donne directement l'identifiant, sans aller chercher
                    # l'objet Activite. "coach" attend un objet : on le retrouve grâce au dictionnaire
                    defaults={"activite_id"         :int(ligne["activite_id"]),
                              "coach"               :utilisateurs[ligne["coach_id"]],
                              # Date et heure restent des chaînes ISO : Django les convertit à l'enregistrement
                              "date"                :ligne["date"],
                              "heure_debut"         :ligne["heure_debut"],
                              "duree_minutes"       :int(ligne["duree_minutes"]),
                              "lieu"                :ligne["lieu"],
                              "places"              :int(ligne["places"]),
                              "niveau"              :ligne["niveau"],
                              "description"         :ligne["description"]},  
                )
                print(seance, "créée" if cree else "mise à jour")
            print()

        # ---------- 4. Inscriptions (en dernier : elles référencent comptes et séances) ----------
        with open(file / "actions.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                inscription, cree = Inscription.objects.update_or_create(
                    id=int(ligne["id"]),
                    defaults={"utilisateur"         :utilisateurs[ligne["utilisateur_id"]],
                              "seance_id"           :int(ligne["objet_id"]),
                              "etat"                :ligne["etat"],
                              # Les dates du fichier sont CONSERVÉES (parse_datetime puis make_aware) :
                              # le tri des inscriptions et la file d'attente en dépendent
                              "date_creation"       :timezone.make_aware(parse_datetime(ligne["date_creation"])),
                              "date_modification"   :timezone.make_aware(parse_datetime(ligne["date_modification"]))},
                )
                print(inscription, "créée" if cree else "mise à jour")
            print()

