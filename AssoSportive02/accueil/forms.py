"""
forms.py : formulaires de connexion et d'inscription.

Les deux formulaires héritent de formulaires fournis par Django, qui gèrent déjà
la validation et la sécurité des mots de passe :
  - AuthenticationForm : vérifie l'identifiant et le mot de passe (connexion).
  - UserCreationForm   : crée un compte (champs password1 / password2, règles de
                         robustesse du mot de passe, hachage à l'enregistrement).

OPTIONS UTILISÉES
  class Meta          Configure un formulaire lié à un modèle :
    model             le modèle à remplir (Utilisateur).
    fields            la liste BLANCHE des champs affichés. Le champ `role` n'y
                      figure pas volontairement : un visiteur ne peut pas se
                      donner le rôle de coach en forgeant la requête.
    widgets           personnalise la balise HTML d'un champ (ici un sélecteur
                      de date, type="date").
  self.fields         Dictionnaire des champs, modifiable dans __init__ (labels,
                      aide, attributs HTML).
  widget.attrs        Attributs HTML ajoutés à un champ (ici la classe CSS).
  help_text           Texte d'aide sous le champ ; vidé ici pour alléger l'affichage.
  label               Intitulé affiché devant le champ.

POURQUOI LES CLASSES TAILWIND SONT DANS LE FORMULAIRE
  Les gabarits affichent les champs avec {{ form.as_p }} : on ne peut donc pas
  écrire de classes CSS dans le HTML. On les ajoute ici via widget.attrs, ce qui
  garde le style au plus près de la définition des champs.
"""

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Utilisateur
from django import forms


class Formulaire_connexion(AuthenticationForm):
    """Formulaire de connexion : identifiant et mot de passe, avec style Tailwind."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Même classe CSS sur tous les champs du formulaire
        for champ in self.fields.values():
            champ.widget.attrs["class"] = "w-full p-3 border border-gray-300 rounded-lg"
        self.fields["username"].label = "Identifiant / Email"
        self.fields["password"].label = "Mot de passe"


class Formulaire_inscription(UserCreationForm):
    """
    Formulaire de création de compte adhérent.

    Le rôle n'est pas demandé : il prend la valeur par défaut du modèle
    ("utilisateur"). Le mot de passe est haché par UserCreationForm.save().
    """
    class Meta:
        model = Utilisateur
        # Seuls ces champs peuvent être saisis par le visiteur
        fields = ("username", "first_name", "last_name", "email", "certificat_jusqu_au")
        # Affiche un calendrier au lieu d'un champ texte
        widgets = {
            "certificat_jusqu_au": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for champ in self.fields.values():
            # Supprime les textes d'aide par défaut de Django (règles du mot de passe...)
            champ.help_text = ""
            champ.widget.attrs["class"] = "w-full p-3 border border-gray-300 rounded-lg"

        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["first_name"].label = "Prénom"
        self.fields["last_name"].label = "Nom"
        self.fields["email"].label = "Email"
        self.fields["certificat_jusqu_au"].label = "Certificat médical valide jusqu'au"
        self.fields["password1"].label = "Mot de passe"
        self.fields["password2"].label = "Confirmer le mot de passe"
        
        
        