#!/bin/bash
set -e

# Se placer dans le dossier du script (là où se trouve manage.py)
cd "$(dirname "$0")"

# Charger les variables du .env
set -a
source .env
set +a

python manage.py makemigrations
python manage.py migrate

# Superuser : créé seulement s'il n'existe pas encore
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
nom = os.environ['DJANGO_SUPERUSER_USERNAME']
if not User.objects.filter(username=nom).exists():
    User.objects.create_superuser(
        nom,
        os.environ['DJANGO_SUPERUSER_EMAIL'],
        os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
    print('Superuser créé')
else:
    print('Superuser déjà présent')
"

python manage.py charger_donnees
python manage.py runserver