# Avis sur l'utilité du projet

## Ce que momem fait concrètement

Si on enlève le vocabulaire, momem est un **gestionnaire de copie de fichiers** : il copie des scripts Python d'un dossier central vers des projets, et les re-copie quand ils changent. C'est utile, mais il faut voir si des solutions existantes ne font pas déjà le travail.

## Alternatives sérieuses

### 1. `pip install -e /chemin/local/utils`
Probablement le **concurrent le plus direct**. On crée un package local `utils` avec un `pyproject.toml` minimal, et on l'installe en mode éditable dans chaque projet :

```bash
pip install -e /chemin/vers/mon-utils
```

**Avantages** :
- Les changements sont reflétés immédiatement (pas besoin de `update`)
- Pas de duplication de fichiers
- Imports Python standards, outillage standard
- Pas d'outil supplémentaire à installer

**Inconvénient** (celui cité dans le DESIGN) : si un projet doit devenir public, il faut alors embarquer le code. Mais c'est aussi le cas avec momem — sauf que momem a déjà copié le code dans le projet.

### 2. `pip install git+https://github.com/user/utils.git`
Même idée, mais depuis un repo git. Pas besoin de PyPI, pas besoin de publier un package. Un simple `pip install --upgrade` met à jour. Compatible avec `requirements.txt` et `pyproject.toml`.

### 3. Git submodules / subtree
- **Submodules** : pénibles à gérer, mais fonctionnels.
- **Subtree** : copie le code dans le projet (comme momem), avec l'historique git en bonus. `git subtree pull` fait l'équivalent de `momem update`.

### 4. Vendoring
Pratique courante (pip lui-même vendor ses dépendances). Il existe des outils comme `vendoring` qui automatisent ça. C'est exactement le pattern de momem, mais avec un outillage existant.

## Où momem apporte une vraie valeur

Malgré ces alternatives, momem a **un avantage spécifique** : il cible le cas d'usage de **bouts de code éparpillés qui ne forment pas un package cohérent**. Les alternatives ci-dessus supposent qu'on a un repo ou package "utils" structuré. Si on a juste un `retry_decorator.py` ici, un `csv_parser.py` là, et un `logging_setup.py` ailleurs, aucun des outils ci-dessus ne gère ça naturellement.

Mais cet avantage a un revers : **est-ce que ça ne serait pas mieux de simplement structurer ces snippets dans un petit package local ?** Un `pyproject.toml` + un dossier avec les scripts, et `pip install -e .` fait le reste. L'effort initial est minime et on bénéficie de tout l'écosystème Python.

## Préoccupations sur le design

1. **Duplication de code** : chaque projet a sa propre copie. Si on a 10 projets, on a 10 copies. Les modifications locales accidentelles créent de la divergence silencieuse.

2. **Le namespace `momem`** — RÉSOLU : le package interne de l'outil CLI a été renommé en `momemcli`. La commande et le nom PyPI restent `momem`, mais il n'y a plus de conflit avec le dossier `momem/` des snippets dans les projets. De plus, les imports entre snippets utilisent des imports relatifs (réécrits automatiquement au `memorize`), ce qui les rend indépendants du namespace.

3. **Pas de versioning** : on ne peut pas dire "ce projet utilise la version X de tel snippet". `momem update` écrase avec la dernière version. Si un snippet change de manière incompatible, tous les projets cassent au prochain `update`.

4. **Gestion des `__init__.py`** : momem doit créer/maintenir les `__init__.py` dans l'arborescence installée pour que les imports fonctionnent. C'est de la plomberie que pip gère nativement.

## Verdict

Le problème est réel — on a tous des bouts de code qu'on réutilise. Mais la solution la plus simple est souvent la meilleure :

- **Si les snippets sont liés** : les mettre dans un petit package local, `pip install -e .`, terminé.
- **Si c'est du one-shot** : un simple copier-coller suffit, pas besoin d'outillage.

Momem se situe entre les deux, dans une niche où on a assez de snippets pour vouloir automatiser, mais pas assez pour justifier un package. **Cette niche existe**, mais elle est étroite. Le risque est de construire un outil plus complexe que le problème qu'il résout.
