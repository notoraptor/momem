# Revue complète du projet momem

## Vue d'ensemble

**momem** est un outil CLI pour gérer et réutiliser des snippets Python entre projets indépendants. Il maintient une base de code locale (`~/.momem/`) et copie les fichiers dans les projets avec résolution automatique des dépendances.

## Santé du projet

| Métrique | Résultat |
|---|---|
| Tests | **114 passed**, 0 failed |
| Couverture | **100%** sur les 409 lignes |
| Linter (ruff) | **0 erreur** |
| LOC source | ~615 lignes (5 modules) |
| LOC tests | ~893 lignes (5 fichiers) |

Le projet est en excellent état technique. Tout est vert.

## Architecture (5 modules)

| Module | Rôle | Lignes |
|---|---|---|
| `cli.py` | Interface Click (7 commandes) | 142 |
| `config.py` | Gestion config globale/locale YAML | 118 |
| `codebase.py` | memorize, forget, show | 116 |
| `project.py` | install, uninstall, update, show | 201 |
| `deps.py` | Parsing AST des imports, résolution dépendances | 134 |

La séparation des responsabilités est claire et bien respectée. Chaque module a un rôle unique.

## Points forts

1. **Couverture de tests exemplaire** : 100% avec des tests unitaires ET d'intégration (CliRunner + subprocess). Les edge cases sont bien couverts (conflits, force, dépendances manquantes, cycles, nettoyage de dossiers).

2. **Gestion des dépendances intelligente** : le parsing AST des imports `momem.*` avec réécriture automatique en imports relatifs au `memorize` est élégant. La résolution récursive avec détection de cycles fonctionne.

3. **Design pragmatique** : la hiérarchie de config (local > global > défaut) et le nettoyage automatique des dossiers vides sont bien pensés.

4. **Code propre** : pas de code mort, pas de sur-ingénierie, nommage clair, docstrings utiles en anglais.

## Points d'attention / Problèmes potentiels

### 1. ~~Bug potentiel : `get_codebase_dir()` ajoute `/momem` deux fois~~ RESOLU

`get_codebase_dir()` utilise maintenant le chemin configuré directement, sans ajouter `/momem`. Le défaut reste `~/.momem/momem`. Documenté dans l'aide CLI, DESIGN.md, PLAN.md et CLAUDE.md.

### 2. ~~`update` compare le contenu mais pas la direction du changement~~ RESOLU

`update` utilise maintenant un hash SHA-256 stocké dans `.momem.yaml` au moment de l'install pour une comparaison 3-way :
- Local inchangé, codebase changée -> mise à jour automatique
- Local modifié, codebase inchangée -> skip (modification locale préservée)
- Les deux changés -> conflit (requiert `--force`)

### 3. `memorize` avec chemin relatif sans `dest` — chemin dépend du CWD

`codebase.py:43` : `rel_dest = dest if dest else str(source_path)`. Si le chemin est relatif (ex: `../../utils/script.py`), il sera stocké avec ce chemin relatif brut dans la codebase, donnant `~/.momem/momem/../../utils/script.py`. C'est problématique. Le DESIGN.md documente ce comportement pour les chemins absolus (d'où l'exigence de `dest`), mais le même problème existe pour les chemins relatifs contenant `..`.

### 4. Pas de gestion des imports de sous-packages dans `deps.py`

La codebase stocke les fichiers `.py` mais n'y crée pas de `__init__.py`. `deps.py` résout tout en `.py`, donc `from .subpackage import something` chercherait `subpackage.py`, pas `subpackage/__init__.py`. Les imports de packages (sous-dossiers) ne sont pas supportés.

### 5. PLAN.md est obsolète

`docs/PLAN.md` référence encore `momem/` comme package principal et `momem.cli:main` comme entry point, alors que le package a été renommé en `momemcli/`. Ce document n'est pas synchronisé avec le code actuel.

### 6. Sécurité des chemins

Pas de validation que les chemins ne sortent pas de la codebase via path traversal (ex: `momem memorize script.py ../../../etc/something`). Risque faible (outil local), mais à noter.

## Suggestions d'amélioration

1. **Résoudre/normaliser les chemins relatifs** dans `memorize` quand `dest` n'est pas fourni — utiliser `Path(source).resolve().relative_to(cwd)` ou similaire pour éviter des chemins avec `..`.

2. ~~**Revoir la sémantique de `update` sans `--force`**~~ — FAIT : comparaison 3-way via hash SHA-256 stocké dans `.momem.yaml`.

3. **Mettre à jour `docs/PLAN.md`** pour refléter le renommage `momem/` → `momemcli/`.

4. **Ajouter une commande `momem diff`** pour voir les différences entre la version installée et la version dans la codebase avant de faire `update --force`.

## Verdict

Le projet est **bien conçu et bien implémenté** pour sa taille. Le code est propre, les tests sont excellents, l'architecture modulaire est claire. Les points d'attention soulevés sont des améliorations de design plutôt que des bugs bloquants. Le projet remplit son cahier des charges tel que défini dans DESIGN.md et PLAN.md.
