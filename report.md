# Avis complet sur le README

## Ce qui est bien

- **Le problème est clairement posé.** La comparaison avec les alternatives (PyPI, projet "utils" local) est pertinente et justifie bien l'existence de l'outil.
- **L'interface CLI est intuitive.** Les noms de commandes (`memorize`, `forget`, `install`, `update`) sont parlants et cohérents avec le nom "momem" (mo-mem, memorize).
- **La séparation config globale / locale** est un bon choix, calqué sur le modèle de git.

## Points à clarifier ou améliorer

### 1. Gestion des chemins absolus — RÉSOLU
Si le chemin vers le bout de code est absolu, `momem memorize` exige le second argument (chemin relatif dans la base de code momem). Cela évite de reproduire des arborescences absolues dans la base de code.

### 2. Convention `PROJECT_DIR/PROJECT_DIR/momem` — RÉSOLU
Ajout d'une config globale `default_project_dir` :
- `None` (défaut) : utilise le nom du dossier du projet → `PROJECT_DIR/PROJECT_DIR/momem`
- Un nom précis (ex. `"src"`) : → `PROJECT_DIR/src/momem`

La config locale `momemdir` reste prioritaire pour les cas particuliers.

Hiérarchie de résolution : **config locale `momemdir` > config globale `default_project_dir` > convention par défaut (nom du projet)**.

La documentation devra expliquer cette convention et comment la configurer.

### 3. `momem show` — RÉSOLU
Ajouter `momem show` (ou `momem show --local`) pour afficher les snippets installés dans le projet courant, en complément de `momem show --memory` qui affiche la base de code globale.

### 4. Gestion des conflits — RÉSOLU
En cas de conflit (fichier déjà existant lors d'un `memorize`, ou fichier local modifié lors d'un `update`), momem signale l'erreur et refuse l'opération. Passer `--force` pour écraser.

### 5. Dépendances entre snippets — RÉSOLU
Les dépendances sont calculées à la volée via `ast.parse` (détection des imports `momem.*`), pas de fichier de métadonnées séparé.

- À l'`install` : parse le script, détecte les imports `momem.*`, résout et installe les dépendances récursivement (avec détection de cycles).
- À l'`update` : re-parse et met à jour l'arbre de dépendances.
- Au `memorize` : validation que les dépendances `momem.*` référencées existent dans la base de code, avertissement sinon.

### 6. Portée limitée à Python — RÉSOLU
L'outil est Python-centric, ce qui est cohérent avec la gestion des dépendances via `ast.parse` (point 5).

### 7. Petites coquilles — RÉSOLU
Corrigées dans le README.

## Suggestion globale — RÉSOLU
Le README a été renommé en `DESIGN.md` car il s'agit d'un cahier des charges / spec de conception. Un vrai README sera créé quand l'outil sera fonctionnel.
