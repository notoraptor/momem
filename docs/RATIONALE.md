# Pourquoi momem ?

## Le problème

On a souvent des petits scripts, fonctions ou classes Python qu'on réutilise à travers plusieurs projets indépendants : un décorateur de retry, un parser CSV, un setup de logging... Ces bouts de code ne forment pas un ensemble cohérent justifiant un package, mais on les copie régulièrement d'un projet à l'autre.

## Les solutions existantes

### 1. Package local avec `pip install -e`

On crée un package local `utils/` avec un `pyproject.toml` minimal et on l'installe en mode éditable :

```bash
pip install -e /chemin/vers/mon-utils
```

| | |
|---|---|
| **Avantages** | Changements reflétés immédiatement, pas de duplication, imports standards, aucun outil supplémentaire |
| **Inconvénients** | Dépend d'un chemin local — le projet n'est pas auto-suffisant. Si on le distribue (GitHub, collègue, déploiement), il faut embarquer le code manuellement. Suppose que les snippets forment un package cohérent. |

### 2. Package git avec `pip install git+url`

Même idée, mais hébergé sur un repo git :

```bash
pip install git+https://github.com/user/utils.git
```

| | |
|---|---|
| **Avantages** | Pas besoin de PyPI, compatible `requirements.txt` et `pyproject.toml`, `pip install --upgrade` pour mettre à jour |
| **Inconvénients** | Dépend de l'accessibilité du repo. Suppose un package structuré. Pas de gestion granulaire (on installe tout ou rien). |

### 3. Git submodules / subtree

| | |
|---|---|
| **Submodules** | Fonctionnels mais pénibles à gérer. Le projet dépend du repo source. |
| **Subtree** | Copie le code dans le projet avec l'historique git. `git subtree pull` met à jour. Le projet est auto-suffisant. |

| | |
|---|---|
| **Avantages subtree** | Auto-suffisant, historique conservé, outillage git standard |
| **Inconvénients subtree** | Commandes git complexes, pas de gestion des dépendances entre fichiers, pas de détection de conflits granulaire. Suppose un repo source structuré. |

### 4. Vendoring

Pratique courante (pip lui-même vendor ses dépendances). Des outils comme `vendoring` automatisent la copie.

| | |
|---|---|
| **Avantages** | Pattern éprouvé, projet auto-suffisant |
| **Inconvénients** | Outillage orienté packages entiers, pas fichiers individuels. Pas de gestion des dépendances entre snippets. |

### 5. Copier-coller

| | |
|---|---|
| **Avantages** | Zéro outillage, immédiat |
| **Inconvénients** | Aucun suivi des mises à jour. Les copies divergent silencieusement. Fastidieux dès qu'on a plus d'une poignée de fichiers. |

## L'approche de momem

momem cible un cas d'usage spécifique : des **bouts de code éparpillés qui ne forment pas un package cohérent**. Un `retry_decorator.py` ici, un `csv_parser.py` là, un `logging_setup.py` ailleurs.

Plutôt qu'un package à structurer et maintenir, momem fonctionne comme un **gestionnaire de fichiers individuels** avec :

- **Base de code locale** (`~/.momem/momem/`) : un dossier central où on accumule ses snippets au fil du temps, sans contrainte de structure
- **Installation par copie** : les snippets sont copiés dans chaque projet, qui reste auto-suffisant et distribuable
- **Dépendances automatiques** : les imports entre snippets sont détectés par parsing AST et résolus récursivement
- **Mise à jour intelligente** : comparaison 3-way (hash à l'install) qui préserve les modifications locales et détecte les vrais conflits
- **Imports relatifs** : réécrits automatiquement au `memorize`, fonctionnent quel que soit le chemin d'installation

### Comparaison résumée

| Critère | pip -e | pip git+url | subtree | vendoring | copier-coller | **momem** |
|---|---|---|---|---|---|---|
| Projet auto-suffisant | Non | Non | Oui | Oui | Oui | **Oui** |
| Granularité fichier | Non | Non | Non | Non | Oui | **Oui** |
| Détection de conflits | — | — | Git | — | Non | **3-way** |
| Dépendances entre fichiers | pip | pip | Non | Non | Non | **AST** |
| Mise à jour automatique | Immédiate | pip upgrade | git pull | Outil | Manuelle | **momem update** |
| Outillage requis | pip | pip + git | git | Outil | Aucun | **momem** |
| Snippets éparpillés | Non | Non | Non | Non | Oui | **Oui** |

## Compromis assumés

1. **Duplication de code** : c'est le principe même de momem, et c'est un avantage — chaque projet est auto-suffisant. Le risque de divergence est atténué par `momem update` et la détection de conflits.

2. **Pas de versioning** : momem ne gère pas de versions, contrairement à pip. La comparaison 3-way (hash stocké, version locale, version codebase) compense partiellement en détectant les modifications locales et les conflits.

3. **Plomberie `__init__.py`** : momem crée et maintient automatiquement les `__init__.py` dans la codebase et les projets. C'est de la plomberie que pip gère nativement, mais c'est transparent pour l'utilisateur.

4. **Niche étroite** : momem se situe entre le copier-coller et le package structuré. Si les snippets sont suffisamment liés pour former un package, `pip install -e` est plus simple. Si c'est du one-shot, un copier-coller suffit. Momem vaut le coup quand on a assez de snippets éparpillés pour vouloir automatiser, mais pas assez de cohérence pour justifier un package.
