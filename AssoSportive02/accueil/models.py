"""
models.py : modèles de données de l'application (une classe = une table).

Chaque attribut de classe est une colonne. Les migrations (makemigrations puis
migrate) traduisent ces classes en tables SQLite : aucune requête SQL n'est
écrite à la main, tout passe par l'ORM.

Correspondance avec le MCD (docs/mcd.md) :
    Utilisateur -> UTILISATEUR    Activite    -> ACTIVITE
    Seance      -> SEANCE         Inscription -> INSCRIPTION

OPTIONS DE CHAMPS UTILISÉES
  max_length          Longueur maximale d'un CharField (obligatoire).
  unique=True         Valeur unique dans la table (ici l'e-mail).
  null=True           La colonne accepte NULL en base.
  blank=True          Le champ peut rester vide dans un formulaire. Pour un
                      champ facultatif, on met les deux (null ET blank).
  default=...         Valeur par défaut à la création.
  choices=...         Liste de couples (valeur stockée, libellé affiché).
                      Django ajoute alors la méthode get_<champ>_display()
                      qui renvoie le libellé lisible.
  ForeignKey          Relation "plusieurs vers un" (clé étrangère).
  on_delete=PROTECT   Interdit la suppression d'un objet encore référencé
                      (ex. une activité qui a des séances) : l'historique ne
                      peut pas être perdu par accident.
  limit_choices_to    Restreint les choix proposés dans les formulaires et
                      l'admin. Ce n'est PAS une contrainte en base de données.
  PositiveIntegerField  Entier supérieur ou égal à 0.
  DateField / TimeField / DateTimeField  Date, heure, date + heure.
  Meta.unique_together  Unicité d'un COUPLE de champs.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Utilisateur(AbstractUser):
    """
    Compte du site : adhérent ou coach, distingués par le champ `role`.

    On étend AbstractUser pour profiter de l'authentification de Django
    (mot de passe haché, connexion, permissions) et on ajoute nos propres champs.
    Cette classe doit être déclarée comme modèle utilisateur du projet
    (AUTH_USER_MODEL dans settings.py).
    """

    # (valeur stockée en base, libellé affiché)
    ROLE_CHOICES = (
        ('gestionnaire', 'Coach'),
        ('utilisateur', 'Adhérant'),
    )
    # AbstractUser a déjà un champ email, mais non unique
    email = models.EmailField(unique = True)
    # Par défaut, tout nouveau compte est un adhérent
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='utilisateur')
    certificat_jusqu_au = models.DateField( null= True, blank = True)

    def __str__(self):
        """Texte affiché pour un utilisateur (admin, listes déroulantes, gabarits)."""
        return f"{self.first_name} {self.last_name} ({self.email})"

class Activite(models.Model):
    """Une discipline sportive proposée par l'association (ex. natation, escalade)."""
    nom = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.nom}"

class Seance(models.Model):
    """Une séance planifiée : une activité, animée par un coach, à une date et une heure."""
    niveau_choix = (
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('tous', 'Tout niveau'),
    )
   # PROTECT : on ne peut pas supprimer une activité ou un coach qui a des séances
    activite = models.ForeignKey(Activite, on_delete=models.PROTECT)
    # limit_choices_to : seuls les comptes "gestionnaire" sont proposés comme coach
    coach = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, limit_choices_to = {'role': 'gestionnaire'})
    # Date et heure sont séparées : on les recombine pour comparer à l'instant présent
    date = models.DateField()
    heure_debut = models.TimeField()
    duree_minutes = models.IntegerField()
    lieu = models.CharField(max_length = 175)
    # Capacité maximale (PositiveInteger : jamais négative)
    places = models.PositiveIntegerField()
    niveau = models.CharField(max_length=50, choices=niveau_choix)
    description = models.TextField()

    def __str__(self):
        return f"{self.activite} {self.date} {self.heure_debut} {self.lieu} {self.places} {self.niveau} {self.description}"

class Inscription(models.Model):
    """
    Lien entre un adhérent et une séance, avec un état.

    États : inscrit, liste_attente, present, absent, annule (fiche A3 du brief).
    """
    etat_choix = (
        ('inscrit', 'Inscrit'),
        ('liste_attente', "Liste d'attente"),
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('annule', 'Annulé'),
    )

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT)
    seance = models.ForeignKey(Seance, on_delete=models.PROTECT)
    # Toute nouvelle inscription démarre à l'état "inscrit" (la vue peut la placer en liste d'attente)
    etat = models.CharField(max_length=50, choices=etat_choix, default='inscrit')
    # default=timezone.now (sans parenthèses : la fonction est appelée à chaque création)
    # plutôt que auto_now_add : avec auto_now_add, Django écraserait les dates du CSV
    # lors du chargement des données
    date_creation = models.DateTimeField(default=timezone.now)
    # Pas de mise à jour automatique : les vues renseignent cette date à chaque changement d'état
    date_modification = models.DateTimeField(default=timezone.now)

    class Meta:
        # Un adhérent ne peut avoir qu'UNE ligne par séance. Pour se réinscrire après
        # une annulation, on réactive donc la ligne existante au lieu d'en créer une autre
        unique_together = ('utilisateur', 'seance')

    def __str__(self):
        return f"{self.utilisateur} - {self.seance} - {self.etat}"