from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur

class Formulaire_inscription(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ("username", "first_name", "last_name", "email", "certificat_jusqu_au")