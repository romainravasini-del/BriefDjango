import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime,parse_date
from django.utils import timezone
from accueil.models import Activite, Utilisateur, Seance, Inscription  # nom à adapter à vos modèles

import datetime


class Command(BaseCommand):
    help = "Charge les données CSV dans la base"

    def handle(self, *args, **options):
        file = settings.BASE_DIR.parent / "data" 

        Inscription.objects.all().delete()
        Seance.objects.all().delete()
        Activite.objects.all().delete()
        Utilisateur.objects.filter(is_superuser=False).delete()
        utilisateurs = {}

        with open(file / "utilisateurs.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                utilisateur, cree = Utilisateur.objects.update_or_create(
                    email=ligne["email"],
                    defaults={
                        "username": ligne["email"],
                        "first_name": ligne["prenom"],
                        "last_name": ligne["nom"],
                        "email": ligne["email"],
                        "role": ligne["role"],
                        "certificat_jusqu_au": parse_date(ligne["certificat_valide_jusqu_au"]) if ligne["certificat_valide_jusqu_au"].strip() else None,
                    },
                )
                utilisateur.set_password("demo1234")
                utilisateur.save()
                utilisateurs[ligne["id"]] = utilisateur
                print(utilisateur, "créée" if cree else "mise à jour")

        with open(file / "categories.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                activite, cree = Activite.objects.update_or_create(
                    id=int(ligne["id"]),
                    defaults={"nom"                 :ligne["nom"]},
                )
                print(activite, "créée" if cree else "mise à jour")
            print()

        with open(file / "objets.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                seance, cree = Seance.objects.update_or_create(
                    id=int(ligne["id"]),
                    defaults={"activite_id"         :int(ligne["activite_id"]),
                              "coach"               :utilisateurs[ligne["coach_id"]],
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

        with open(file / "actions.csv", encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                inscription, cree = Inscription.objects.update_or_create(
                    id=int(ligne["id"]),
                    defaults={"utilisateur"         :utilisateurs[ligne["utilisateur_id"]],
                              "seance_id"           :int(ligne["objet_id"]),
                              "etat"                :ligne["etat"],
                              "date_creation"       :timezone.make_aware(parse_datetime(ligne["date_creation"])),
                              "date_modification"   :timezone.make_aware(parse_datetime(ligne["date_modification"]))},
                )
                print(inscription, "créée" if cree else "mise à jour")
            print()

