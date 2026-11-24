from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('gestionnaire', 'Coach'),
        ('utilisateur', 'Adhérant'),
    )
    email = models.EmailField(unique = True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='utilisateur')
    certificat_jusqu_au = models.DateField( null= True, blank = True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class Activite(models.Model):
    nom = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.nom}"

class Seance(models.Model):
    niveau_choix = (
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('tous', 'Tout niveau'),
    )
    activite = models.ForeignKey(Activite, on_delete=models.PROTECT)
    coach = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, limit_choices_to = {'role': 'gestionnaire'})
    date = models.DateField()
    heure_debut = models.TimeField()
    duree_minutes = models.IntegerField()
    lieu = models.CharField(max_length = 175)
    places = models.PositiveIntegerField()
    niveau = models.CharField(max_length=50, choices=niveau_choix)
    description = models.TextField()

    def __str__(self):
        return f"{self.activite} {self.date} {self.heure_debut} {self.lieu} {self.places} {self.niveau} {self.description}"

class Inscription(models.Model):
    etat_choix = (
        ('inscrit', 'Inscrit'),
        ('liste_attente', "Liste d'attente"),
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('annule', 'Annulé'),
    )

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT)
    seance = models.ForeignKey(Seance, on_delete=models.PROTECT)
    etat = models.CharField(max_length=50, choices=etat_choix, default='inscrit')
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('utilisateur', 'seance')

    def __str__(self):
        return f"{self.utilisateur} - {self.seance} - {self.etat}"