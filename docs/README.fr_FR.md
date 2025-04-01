# clang-i18n
Greffon Clang avec prise en charge de l'i18n

## Introduction

Clang-i18n est un plug-in de prise en charge de l'i18n pour Clang visant à fournir des fonctionnalités de localisation pour les diagnostics et les informations d'aide de la chaîne d'outils Clang, afin de mieux répondre aux besoins des utilisateurs non anglophones.
Ce projet ne nécessite pas de modifier le code source de Clang ou de le reconstruire, mais propose des fonctionnalités de traduction à la demande et prêtes à l'emploi sous forme de plug-in.

## Installation

Actuellement, ce projet prend en charge les plateformes Linux x86_64/aarch64/loongarch64/riscv64. Les contributions pour d'autres plateformes sont les bienvenues.
Veuillez vous assurer que Clang a été compilé avec des liens dynamiques (Clang/LLVM installé via Ubuntu apt répond à cette exigence).
Si CMake ne trouve pas l'installation Clang/LLVM, exécutez `sudo apt install llvm-dev libclang-dev` pour installer les fichiers de développement.

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# Si vous devez spécifier la version Clang/LLVM, ajoutez le chemin de recherche à CMake.
# Exemple : -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DClang_DIR=/usr/lib/cmake/clang-20
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## Utilisation

```bash
export LANG=fr_FR.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

De plus, deux variables d'environnement optionnelles contrôlent le comportement de clang-i18n :
- `CLANG_I18N_LANG` : Définir le code langue (ex : fr_FR) pour remplacer la configuration par défaut (par défaut `$LANG` sous Linux).
- `CLANG_I18N_TRANSLATION_DIR` : Définir le répertoire des fichiers de traduction. La valeur par défaut sous Linux est `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, soit `/usr/local/share/clang-i18n/i18n` avec la configuration CMake par défaut.

### Ajouter la prise en charge i18n à clangd sous VSCode

Créez un fichier nommé `clangd-i18n` avec le contenu suivant :
```bash
#!/usr/bin/bash

LANG=fr_FR LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
Assurez-vous que ce fichier est exécutable :
```bash
chmod +x clangd-i18n
```
Ensuite, dans les paramètres VSCode, définissez `clangd.path` vers le chemin de ce fichier :
```
{
    "clangd.path": <chemin vers clangd-i18n>
}
```

## Contribuer de nouvelles traductions

Les contributions de nouvelles traductions ou d'améliorations sont les bienvenues, ainsi que les traductions stylisées.

### Format des fichiers de traduction

Les fichiers de traduction terminent par .yml (non au format YAML) et sont placés dans le répertoire i18n.

Le format est :
```yaml
# Texte anglais original
Hash : Traduction
```

### Traduction automatique avec des modèles de langage

Ce projet supporte l'utilisation de LLM avec des API compatibles OpenAI pour la traduction. Configuration :
```bash
# Installation des dépendances
pip install openai

# Préparer le fichier de prompt i18n/fr_FR.prompt

# Préparer le fichier d'erreurs i18n/fr_FR.errata
# Format :
# <Terme anglais> <Traduction erronée>

export LLM_ENDPOINT=<Point de terminaison LLM>
export LLM_MODEL=<Nom du modèle>
export LLM_TOKEN=<Clé API>

python3 translate.py corpus.txt i18n/fr_FR.prompt i18n/fr_FR.errata i18n/fr_FR.yml <Taille de lot>
```

La taille du lot doit être modérée (recommandé : 20), sinon les traductions peuvent être mal ordonnées.

## Licence

Ce projet est sous licence [MIT](LICENSE).
