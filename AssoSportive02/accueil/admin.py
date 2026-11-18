from django.contrib import admin
from django.contrib.auth.admin import UserAdmin    
from .models import Utilisateur, Inscription, Activite, Seance

admin.site.register(Utilisateur,UserAdmin)
admin.site.register(Inscription)
admin.site.register(Activite)
admin.site.register(Seance)