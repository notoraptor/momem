# Plan d'implémentation momem

## Dépendances à ajouter

- `pyyaml` : lecture/écriture des fichiers de configuration `.momem.yaml`
- `click` : framework CLI (sous-commandes, options, arguments)

## Structure du package

```
momem/
├── __init__.py
├── __main__.py          # Entry point: python -m momem
├── cli.py               # Définition CLI click (commandes et options)
├── config.py            # Lecture/écriture config globale et locale
├── codebase.py          # Opérations sur la base de code (memorize, forget, show)
├── project.py           # Opérations sur le projet local (install, uninstall, update, show)
└── deps.py              # Parsing des dépendances momem.* via ast
```

Entry point dans `pyproject.toml` :
```toml
[project.scripts]
momem = "momem.cli:main"
```

## Phase 1 — Configuration (`config.py`)

### Fichiers de configuration
- **Global** : `~/.momem/.momem.yaml`
- **Local** : `.momem.yaml` dans le répertoire courant

### Clés de configuration
- `codebase` (global) : chemin direct vers la base de code. Défaut : `~/.momem/momem`
- `default_project_dir` (global) : nom du sous-dossier projet. Défaut : `None` (= nom du dossier courant)
- `momemdir` (local) : chemin du dossier d'installation dans le projet. Prioritaire sur tout.

### Résolution du dossier d'installation local
1. Config locale `momemdir` → utilisé tel quel
2. Config globale `default_project_dir` → `PROJECT_DIR/<valeur>/momem`
3. Défaut → `PROJECT_DIR/<nom_du_dossier_projet>/momem`

### Commandes
- `momem config --global --set <clé> <valeur>`
- `momem config --local --set <clé> <valeur>`
- `momem config --show` (afficher la config effective, pour debug)

### Implémentation
- Fonctions : `load_global_config()`, `save_global_config()`, `load_local_config()`, `save_local_config()`
- Fonction : `resolve_install_dir()` — applique la hiérarchie de résolution
- Fonction : `get_codebase_dir()` — retourne le chemin de la base de code
- Création automatique de `~/.momem/` et `~/.momem/momem/` si absents

## Phase 2 — Base de code (`codebase.py`)

### `momem memorize <source> [dest]`
1. Valider que `<source>` existe et est un fichier `.py`
2. Si `<source>` est un chemin absolu, exiger `[dest]` (sinon erreur)
3. Si `[dest]` absent, utiliser le chemin relatif de `<source>` comme destination
4. Calculer le chemin cible : `<codebase_dir>/<dest>`
5. Si le fichier cible existe déjà → erreur (sauf `--force`)
6. Copier le fichier
7. Valider les dépendances `momem.*` via `deps.py` : avertir si une dépendance n'existe pas dans la base

### `momem forget <path>`
1. Résoudre `<path>` dans la base de code
2. Vérifier que le fichier existe (sinon erreur)
3. Supprimer le fichier
4. Nettoyer les dossiers parents vides

### `momem show --memory`
- Afficher l'arborescence des fichiers dans la base de code

## Phase 3 — Dépendances (`deps.py`)

### `find_momem_imports(file_path) -> set[str]`
- Parse le fichier avec `ast.parse`
- Parcourir les nœuds `Import` et `ImportFrom`
- Collecter les imports dont le module racine est `momem`
- Retourner les chemins relatifs des modules dépendants (ex. `momem.utils.foo` → `utils/foo.py`)

### `resolve_dependencies(file_path, codebase_dir) -> list[str]`
- Appeler `find_momem_imports` récursivement
- Détecter les cycles (ensemble de fichiers déjà visités)
- Retourner la liste ordonnée de tous les fichiers à installer

### `validate_dependencies(file_path, codebase_dir) -> list[str]`
- Appeler `find_momem_imports`
- Retourner la liste des dépendances manquantes dans la base de code

## Phase 4 — Projet local (`project.py`)

### `momem install <path> [--force]`
1. Résoudre le dossier d'installation local via `resolve_install_dir()`
2. Résoudre `<path>` dans la base de code (vérifier qu'il existe)
3. Calculer les dépendances via `resolve_dependencies()`
4. Pour chaque fichier (script + dépendances) :
   - Calculer le chemin cible local
   - Si le fichier cible existe → erreur (sauf `--force`)
   - Copier le fichier
5. S'assurer que les `__init__.py` nécessaires existent dans l'arborescence `momem/`

### `momem uninstall <path>`
1. Résoudre le chemin dans le dossier d'installation local
2. Supprimer le fichier (erreur s'il n'existe pas)
3. Nettoyer les dossiers parents vides (sauf le dossier `momem/` racine)

### `momem uninstall --all`
1. Supprimer tout le contenu du dossier `momem/` local
2. Garder le dossier `momem/` avec un `__init__.py` vide (ou supprimer entièrement — à décider)

### `momem update [--force]`
1. Lister tous les fichiers `.py` dans le dossier `momem/` local
2. Pour chaque fichier, comparer avec le hash SHA-256 stocké dans `.momem.yaml` au moment de l'install :
   - Local inchangé, codebase changée → mise à jour automatique
   - Local modifié, codebase inchangée → skip (modification locale préservée)
   - Les deux changés → conflit sans `--force`, écrasement avec `--force`
   - Pas de hash stocké (install antérieur) → mise à jour automatique
3. Re-calculer les dépendances : installer les nouvelles, signaler les obsolètes

### `momem show` / `momem show --local`
- Afficher l'arborescence des fichiers installés dans le projet courant

## Phase 5 — CLI (`cli.py` + `__main__.py`)

### Structure click
```
momem
├── memorize  <source> [dest]  [--force]
├── forget    <path>
├── install   <path>           [--force]
├── uninstall <path> | --all
├── update                     [--force]
├── show      --memory | --local (défaut: --local)
└── config    --global/--local --set <key> <value> | --show
```

### `__main__.py`
```python
from momem.cli import main
main()
```

## Phase 6 — Tests

- `tests/conftest.py` : fixtures (dossier temp pour `~/.momem`, dossier temp pour projet)
- `tests/test_config.py` : lecture/écriture config, résolution install dir
- `tests/test_codebase.py` : memorize, forget, show --memory
- `tests/test_deps.py` : parsing imports, résolution récursive, détection de cycles
- `tests/test_project.py` : install, uninstall, update, show --local
- `tests/test_cli.py` : tests d'intégration via `click.testing.CliRunner`

## Ordre d'implémentation recommandé

1. **Config** — fondation de tout le reste
2. **Codebase** — memorize/forget/show (pas de dépendance sur deps)
3. **Deps** — parsing des imports
4. **Project** — install/uninstall/update (dépend de config, codebase, deps)
5. **CLI** — câblage de toutes les commandes
6. **Tests** — à écrire en parallèle de chaque phase idéalement

Chaque phase peut être commitée indépendamment.
