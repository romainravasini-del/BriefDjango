from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Utilisateur
from django import forms


class Formulaire_connexion(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for champ in self.fields.values():
            champ.widget.attrs["class"] = "w-full p-3 border border-gray-300 rounded-lg"
        self.fields["username"].label = "Identifiant / Email"
        self.fields["password"].label = "Mot de passe"


class Formulaire_inscription(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ("username", "first_name", "last_name", "email", "certificat_jusqu_au")
        widgets = {
            "certificat_jusqu_au": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for champ in self.fields.values():
            champ.help_text = ""
            champ.widget.attrs["class"] = "w-full p-3 border border-gray-300 rounded-lg"

        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["first_name"].label = "Prénom"
        self.fields["last_name"].label = "Nom"
        self.fields["email"].label = "Email"
        self.fields["certificat_jusqu_au"].label = "Certificat médical valide jusqu'au"
        self.fields["password1"].label = "Mot de passe"
        self.fields["password2"].label = "Confirmer le mot de passe"
        
        
        