# AssoSportive02

Application de gestion pour une association sportive, réalisée avec Django dans le cadre du brief « application de gestion avec Django ».

- **Thème choisi** : association sportive
- **Catalogue** : les séances (activité, coach, date, lieu, places, niveau)
- **Demandes** : les inscriptions aux séances
- **Gestionnaire** : le coach
- **Équipe** : groupe de trois personnes, Romain, Benjamin, Loïc


---

## 1. Prérequis

- Python 3.14 (version utilisée pendant le développement) [À CONFIRMER]
- Git
- Un terminal bash (macOS, Linux, ou Git Bash / WSL sous Windows) pour le script `setup.sh`

## 2. Installation

```bash
# 1. Récupérer le projet
git clone <url-du-depot>
cd BriefDjango

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Se placer dans le dossier du projet (celui de manage.py)
cd AssoSportive02
```

## 3. Configuration (fichier `.env`)

Le fichier `.env` n'est **pas versionné** (il contient la clé secrète). Il se crée dans `AssoSportive02/`, à côté de `manage.py`. Voici le modèle :

```
SECRET_KEY='remplacer-par-une-cle-secrete'
DEBUG=True
DATABASE_NAME=db.sqlite3

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD="mot_de_passe_de_dev"
```

Règles de format (le fichier est lu par bash dans `setup.sh`) :

- pas d'espace autour du `=`
- valeur entre guillemets si elle contient des caractères spéciaux (guillemets simples si elle contient un `$`)

## 4. Lancement

### Méthode rapide : `setup.sh`

```bash
chmod +x setup.sh
./setup.sh
```

Le script enchaîne, dans l'ordre :

1. `python manage.py makemigrations`
2. `python manage.py migrate`
3. création du superuser (seulement s'il n'existe pas déjà, donc relançable)
4. `python manage.py charger_donnees` (chargement des CSV)
5. `python manage.py runserver --insecure` (ou `runserver` si `DEBUG=True`)

L'application est ensuite disponible sur <http://127.0.0.1:8000/>.

### Méthode manuelle

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py charger_donnees
python manage.py runserver
```

## 5. Chargement des données

Les fichiers CSV fournis sont dans `data/` (ils ne sont jamais modifiés) :

| Fichier | Contenu |
|---|---|
| `categories.csv` | les activités |
| `utilisateurs.csv` | 20 comptes de démonstration |
| `objets.csv` | les séances |
| `actions.csv` | des inscriptions déjà enregistrées |

La commande `python manage.py charger_donnees` lit ces fichiers et remplit la base.

## 6. Structure du projet

```
BriefDjango/
├── AssoSportive02/
│   ├── accueil/                  # application principale
│   │   ├── management/commands/
│   │   │   └── charger_donnees.py # commande de chargement des CSV
│   │   ├── migrations/
│   │   ├── templates/accueil/    # accueil, connexion, espace membre
│   │   ├── admin.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── AssoSportive02/           # configuration du projet (settings, urls)
│   ├── templates/base.html       # gabarit commun
│   ├── manage.py
│   └── setup.sh
├── data/                         # fichiers CSV fournis
├── docs/
│   └── mcd.md                    # schéma de la base (Mermaid)
├── README.md
└── requirements.txt
```

## 7. Schéma de la base de données

Le schéma relationnel est dans [`docs/mcd.md`](docs/mcd.md) (diagramme Mermaid, affiché directement par GitHub).

## 8. Pages de l'application

| Adresse | Page | Accès |
|---|---|---|
| `/` | Accueil | public |
| `/inscription/` | Création de compte | public |
| `/connexion/` | Connexion | public |
| `/deconnexion/` | Déconnexion (POST) | connecté |
| `/catalogue/` | Liste des séances, recherche, filtre | public |
| `/catalogue/<id>/` | Détail d'une séance | public |
| `/catalogue/<id>/demande/` | Inscription à une séance | connecté |
| `/mes-demandes/` | Mes inscriptions | connecté |
| `/gestion/` | Espace du coach | gestionnaire |


## 9. Règles métier

- On ne s'inscrit pas à une séance déjà passée.
- Si la séance est complète, l'inscription est créée à l'état `liste_attente` au lieu d'être refusée.
- Un adhérent dont le certificat médical est absent ou expiré à la date de la séance ne peut pas s'inscrire (un message l'explique).
- États d'une inscription : `inscrit`, `liste_attente`, `present`, `absent`, `annule`.
- Transitions autorisées : voir la fiche A3 du brief. Toute transition non prévue est bloquée côté serveur par un dictionnaire `TRANSITIONS_AUTORISEES` dans `Gestion_transition_view` (et par vérification du propriétaire/rôle dans `Annuler_inscription_view`).

## 10. Choix techniques et justifications

- **Découpage en applications** : une application principale unique (`accueil`) regroupant les modèles, formulaires, vues, URLs, templates et la commande de chargement, afin de garder une architecture simple et lisible.
- **Représentation du rôle et de l'information propre au compte (certificat médical)** : modèle utilisateur personnalisé `Utilisateur` héritant d'`AbstractUser` (`AUTH_USER_MODEL = "accueil.Utilisateur"`), avec `role` (`utilisateur` / `gestionnaire`) et `certificat_jusqu_au` (`DateField`, nullable pour les coachs).
- **Blocage des changements d'état interdits** : contrôle d'accès par `GestionnaireRequiredMixin` (`UserPassesTestMixin`, renvoyant `403` aux non-gestionnaires) et validation stricte des transitions côté serveur via `TRANSITIONS_AUTORISEES`.
- **Commande de chargement relançable** : `charger_donnees.py` utilise `update_or_create` dans l'ordre des dépendances (`utilisateurs.csv`, `categories.csv`, `objets.csv`, `actions.csv`), conserve les dates conscientes du fuseau horaire (`timezone.make_aware`) et hache les mots de passe (`set_password`).
- **Vues basées sur des classes** : utilisation des vues génériques Django (`TemplateView`, `FormView`, `ListView`, `DetailView`, `View`) combinées à `LoginRequiredMixin` et `UserPassesTestMixin`.

## 11. Vérification

La cohérence du jeu de données CSV est vérifiée avec `python data/verifier_donnees.py`, et le projet Django avec `python manage.py check` ainsi que des tests manuels dans le navigateur (parcours adhérent, certificat expiré, liste d'attente, annulation avec promotion automatique, et parcours coach `/gestion/` avec contrôle `403`).

## 12. Organisation du travail

- Dépôt Git avec une branche `develop` et des branches par fonctionnalité (`feature/...`), avec revues et fusions régulières en équipe.
