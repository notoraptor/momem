# momem

Gestionnaire de snippets Python réutilisables entre projets.

## Le problème

On a tous des bouts de code Python qu'on copie d'un projet à l'autre : un décorateur de retry, un parser CSV, un setup de logging... Trop éparpillés pour en faire un package, trop utilisés pour les copier-coller à la main.

## La solution

`momem` maintient une base de code locale (`~/.momem/`) et gère l'installation, la mise à jour et la suppression de snippets dans chaque projet. Les snippets sont copiés localement : chaque projet reste auto-suffisant et distribuable.

## Installation

```bash
pip install momem
```

Requiert Python 3.13+.

## Commandes

```
momem memorize <source> [dest]   # Ajouter un snippet à la base
momem install <path>             # Installer dans le projet courant
momem update                     # Mettre à jour les snippets locaux
momem diff [path]                # Voir les différences local vs codebase
momem show --memory / --local    # Lister les snippets
momem forget <path>              # Retirer de la base
momem uninstall <path> / --all   # Retirer du projet
momem config --global/--local    # Gérer la configuration
```

## Utilisation rapide

### Ajouter un snippet à la base

```bash
momem memorize utils/retry.py
```

Le fichier est copié dans la base de code locale. Si le fichier est hors du dossier courant, un chemin de destination est requis :

```bash
momem memorize /chemin/absolu/retry.py utils/retry.py
```

### Installer dans un projet

```bash
cd mon-projet
momem install utils/retry.py
```

Le snippet est copié dans le dossier d'installation du projet (par défaut `mon-projet/mon-projet/momem/`). Les dépendances entre snippets sont détectées automatiquement via parsing AST et installées ensemble.

### Mettre à jour

```bash
momem update
```

Comparaison intelligente en 3 étapes :
- **Codebase modifiée, local intact** : mise à jour automatique
- **Local modifié, codebase intacte** : modifications locales préservées
- **Les deux modifiés** : conflit signalé, `--force` pour écraser

### Voir les différences avant de forcer

```bash
momem diff              # Tous les fichiers installés
momem diff utils/retry.py   # Un fichier spécifique
```

### Autres commandes

```bash
momem show --memory         # Lister les snippets dans la base
momem show --local          # Lister les snippets installés
momem forget utils/retry.py # Retirer de la base
momem uninstall retry.py    # Retirer du projet
momem uninstall --all       # Tout retirer du projet
```

## Configuration

Configuration globale (`~/.momem/.momem.yaml`) et locale (`.momem.yaml` à la racine du projet).

```bash
# Changer le dossier de la base de code
momem config --global --set codebase /chemin/vers/ma-base

# Changer le dossier d'installation local
momem config --local --set momemdir src/mon_package/momem

# Voir la configuration effective
momem config show
```

### Dossier d'installation

Par défaut : `PROJECT_DIR/PROJECT_DIR/momem/` (convention Python où le dossier du projet = le package principal).

Hiérarchie de résolution :
1. Config locale `momemdir` (prioritaire)
2. Config globale `default_project_dir` -> `PROJECT_DIR/<valeur>/momem`
3. Défaut -> `PROJECT_DIR/<nom_du_dossier>/momem`

## Fonctionnalités clés

- **Projets auto-suffisants** : les snippets sont copiés, pas liés. Le projet est distribuable tel quel.
- **Dépendances automatiques** : les imports entre snippets (`from .helper import x`) sont détectés par parsing AST, résolus récursivement, avec détection de cycles.
- **Imports relatifs** : les imports `momem.*` sont réécrits en imports relatifs au `memorize`, fonctionnent quel que soit le chemin d'installation.
- **Sous-packages** : les dossiers avec `__init__.py` sont supportés comme dépendances.
- **Gestion des conflits** : refus par défaut, `--force` pour écraser.
- **Sécurité des chemins** : les destinations sont validées (purement relatives, sans traversée).

## Licence

MIT
