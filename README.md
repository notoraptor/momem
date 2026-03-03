# Problème

J'ai souvent des petits scripts, fonctions ou classes génériques que je souhaite réutiliser à travers plusieurs projets indépendants.
Mais je ne sais jamais comment gérer ces codes à travers tous les projets.

Option PYPI: ces codes ne forment pas un ensemble cohérent justifiant de créer un paquet PYPI.
En outre, ils peuvent changer regulièrement, ce qui serait pénible à gérer s'il faut chaque fois créer le package,
l'uploader, puis le réinstaller dans les projets qui s'en servent.

Option projet Github "utils" local importé dans les autres projets: si un des projets utilisant ces codes doit devenir public,
il faudra y copier manuellement le code partagé, et se souvenir de le recopier lorsqu'il change dans le projet "utils" de base.
Ća peut être pénible, à la longue.

# Proposition de solution: outil `momem`

- l'outil gère une base de code locale avec les options ajout/suppression/mise à jour de bouts de code
  - contrairement à pypi, pas besoin de créer et uploader un package chaque fois. On a juste à gérer localement les fichiers.
  - exemples:
    - `momem memorize <chemin/vers/script>`: ajoute un fichier Python à la base de code
    - `momem forget <chemin/vers/script>`: supprime un fichier Python de la base de code
    - `momem show --memory`: affiche l'arbre des codes disponibles dans la base de code
- l'outil permet ensuite de gérer l'installation de bouts de code dans un projet:
  - exemples:
    - `momem install <chemin/vers/script>`: installe le script de la base de code dans le projet local
    - `momem uninstall <chemin/vers/script>`: supprime le script de la base de code présent dans le projet local
    - `momem uninstall --all`: supprime tous les scripts de la base de code présents dans le projet local
    - `momem update`: met à jour tous les scripts locaux copiés depuis la base de code.
  - contrairement au projet github "utils" local, la mise à jour des bouts de code est automatique via `momem update`: 
    pas besoin de les recopier manuellement.

# Mise en oeuvre

## Base de code

L'outil utilise le dossier `TOOLDIR = "~/.momem"`.

La configuration est dans le fichier `TOOLDIR / ".momem.yaml"`

Par défaut, la base de code est stockée dans `TOOLDIR / "momem"`

On peut configurer l'outil pour que sa base de code soit dans un autre dossier, par exemple dans un vrai projet github:

`momem config --global --set codebase my_github_dir`

La base de code sera alors gérée dans `my_github_dir / "momem"`

## Projets locaux

Dans un projet local `PROJECT_DIR`, l'outil installera les bouts de code dans `PROJECT_DIR/PROJECT_DIR/momem`.

Ća devrait permettre de gérer la plupart des projets Python github, dont le nom du dossier est aussi le nom ud package principal.

On peut configurer localement le dossier d'installation des bouts de code:

`momem config --local --set momemdir my_momem_folder`

La configuration locale sera stockée dans un fichier `.momem.yaml` dans le dossier d'exécution de la commande (typiquement, la racine du projet Github)

Les bouts de codes seront alors stockés dans `my_momem_folder`.

## Gestion des chemins vers les bouts de code

Par défaut, à la mémorisation, les chemins vers les bouts de code sont reproduits dans la base de code.

Typiquement, si on fait:

`momem memorize chemin/vers/script.py`

Alors, le script sera copié dans:

`~/.momem/chemin/vers/script.py`

Pareil si le chemin est absolu:

`momem memorize /absolute/chemin/vers/script.py` => `~/.momem/absolute/chemin/vers/script.py`

Et le chemin est reproduit dans les projets locaux. Typiquement:

`PROJET/PROJET/momem/chemin/vers/script.py`

On peut configurer manuellement le chemin de mémorisation:

`momem memorize chemin/vers/script.py chemin/dans/memo.py`

Et c'est le chemin configuré qu'il faudra ensuite utiliser pour référencer ce script. Typiquement:

`momem install chemin/dans/memo.py`
