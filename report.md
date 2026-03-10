# Avis complet sur le README

## Ce qui est bien

- **Le problème est clairement posé.** La comparaison avec les alternatives (PyPI, projet "utils" local) est pertinente et justifie bien l'existence de l'outil.
- **L'interface CLI est intuitive.** Les noms de commandes (`memorize`, `forget`, `install`, `update`) sont parlants et cohérents avec le nom "momem" (mo-mem, memorize).
- **La séparation config globale / locale** est un bon choix, calqué sur le modèle de git.

## Points à clarifier ou améliorer

### 1. Gestion des chemins absolus — risque de confusion
Ligne 75 : `momem memorize /absolute/chemin/vers/script.py` => `~/.momem/absolute/chemin/vers/script.py`

Reproduire un chemin absolu dans la base de code crée une arborescence profonde et peu lisible. Est-ce vraiment souhaitable ? Une alternative serait de ne garder que le nom du fichier (ou un chemin relatif au CWD) par défaut, et d'utiliser le 2e argument pour les cas spéciaux.

### 2. Convention `PROJECT_DIR/PROJECT_DIR/momem` — fragile
Ligne 49-51 : L'hypothèse que le dossier du projet porte le même nom que le package principal est courante mais pas universelle (ex. : projets avec des tirets dans le nom du dossier mais des underscores dans le package, monorepos, projets avec `src/` layout). Ça mériterait d'être documenté plus explicitement comme une convention par défaut, avec un encouragement à configurer via `--local --set momemdir`.

### 3. `momem show` — incomplet
Seul `momem show --memory` est mentionné. Il serait logique d'avoir aussi `momem show` (ou `momem show --local`) pour afficher les snippets installés dans le projet courant. C'est peut-être prévu mais non documenté.

### 4. Pas de gestion des conflits / versions
Que se passe-t-il si :
- On fait `momem update` mais le fichier local a été modifié manuellement ? Écrasement silencieux ? Avertissement ?
- On `memorize` un fichier qui existe déjà dans la base ? Remplacement automatique ?

Ce sont des cas d'usage fréquents qui mériteraient d'être spécifiés.

### 5. Pas de notion de dépendances entre snippets
Si `script_a.py` importe `script_b.py`, `momem install script_a.py` devrait-il aussi installer `script_b.py` ? Si non, ça peut créer des `ImportError` silencieux. Au minimum, ça mérite une mention.

### 6. Portée limitée à Python ?
Le README parle de "fichier Python" mais le mécanisme de copie de fichiers est fondamentalement agnostique du langage. Est-ce intentionnellement limité à Python, ou est-ce que ça pourrait gérer n'importe quel fichier ? Si c'est Python-only, pourquoi ?

### 7. Petites coquilles
- Ligne 12, 51 : "Ća" → "Ça"
- Ligne 51 : "le nom ud package" → "le nom du package"
- Ligne 7 : "regulièrement" → "régulièrement"
- Ligne 31 : "Mise en oeuvre" → "Mise en œuvre"

## Suggestion globale

Le README ressemble plus à une **note de conception / spec** qu'à un vrai README. Pour un projet public, il faudrait éventuellement le restructurer avec : une description concise en haut, un exemple d'utilisation rapide, puis les détails. Mais si c'est un outil personnel et que ce document sert de spec de développement, c'est très bien en l'état.
