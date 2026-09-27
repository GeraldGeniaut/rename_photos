# renomme_photos.py

Petit script Python qui renomme les photos d'un dossier (typiquement `DSC_0002.JPG` en sortie d'appareil) selon le format :

```
PREFIXE-AAAAMMJJ-NNN.EXT
```

| Élément    | Signification                                                        |
|------------|----------------------------------------------------------------------|
| `PREFIXE`  | Préfixe libre choisi à l'exécution (ex : `N`)                        |
| `AAAAMMJJ` | Date de la prise de vue                                              |
| `NNN`      | Compteur sur 3 chiffres, repart à `001` pour chaque jour             |
| `EXT`      | Extension d'origine, mise en majuscules (`.JPG`)                     |

Exemple :

```
DSC_0001.JPG  (2026-08-01 12:00:00)  =>  N-20260801-001.JPG
DSC_0002.JPG  (2026-08-01 12:05:00)  =>  N-20260801-002.JPG
DSC_0003.JPG  (2026-08-02 09:30:00)  =>  N-20260802-001.JPG
```

## Fonctionnement

**Date de prise de vue.** Le script lit le champ EXIF `DateTimeOriginal` écrit par l'appareil. La date de création du fichier n'est pas utilisée, car elle est remplacée par la date de copie lorsqu'on transfère les photos de la carte vers le disque. Si une photo n'a pas de données EXIF, le script se rabat sur la date de modification du fichier et le signale dans la sortie par la mention `[date fichier, pas d'EXIF]`.

**Numérotation.** Les photos sont triées par ordre chronologique de prise de vue, puis numérotées jour par jour. Si deux photos ont exactement la même seconde, le nom de fichier d'origine sert de départage.

**Imports successifs.** Les fichiers déjà renommés avec le même préfixe sont détectés et laissés tels quels. La numérotation des nouvelles photos reprend à la suite : si `N-20260801-012.JPG` existe déjà, la photo suivante du même jour devient `N-20260801-013.JPG`.

**Sécurité.** Aucun fichier n'est jamais écrasé : si le nom cible existe déjà, la photo est ignorée et une erreur est affichée. Le mode simulation permet de vérifier le résultat avant tout renommage.

**Fichiers traités.** Extensions `.jpg` et `.jpeg` (insensible à la casse), dans le dossier indiqué uniquement (pas de sous-dossiers).

## Prérequis

- Python 3.8 ou supérieur
- [Pillow](https://pypi.org/project/Pillow/) pour la lecture des EXIF

Sous Windows, si `pip` n'est pas dans le PATH, passer par le lanceur `py` :

```powershell
py -m pip install Pillow
```

Vérification :

```powershell
py -c "import PIL; print(PIL.__version__)"
```

Sans Pillow, le script fonctionne quand même mais utilise les dates des fichiers, ce qui donne des résultats faux sur des photos copiées.

## Utilisation

```
py renomme_photos.py DOSSIER --prefixe PREFIXE [--simulation]
```

| Option              | Description                                               |
|---------------------|-----------------------------------------------------------|
| `DOSSIER`           | Dossier contenant les photos à renommer                   |
| `-p`, `--prefixe`   | Préfixe à utiliser (obligatoire)                          |
| `-s`, `--simulation`| Affiche les renommages prévus sans rien modifier          |

Il est conseillé de toujours lancer une simulation d'abord :

```powershell
py .\renomme_photos.py "U:\Appareil-Nikon\a traiter" --prefixe N --simulation
py .\renomme_photos.py "U:\Appareil-Nikon\a traiter" --prefixe N
```

## Pièges connus sous Windows

**Pas de `\` avant le guillemet fermant.** Dans `"U:\Photos\a traiter\"`, la séquence `\"` est interprétée comme un guillemet littéral : tout le reste de la ligne est alors avalé dans le nom du dossier, et le script signale que `--prefixe` est manquant. Écrire le chemin sans backslash final : `"U:\Photos\a traiter"`.

**« Python est introuvable… Microsoft Store ».** Windows installe de faux `python.exe` / `python3.exe` qui redirigent vers le Store. Les désactiver dans *Paramètres > Applications > Paramètres d'applications avancés > Alias d'exécution d'application*, ou forcer la version avec `py -3.12 .\renomme_photos.py ...`.

**Caractères interdits dans le préfixe.** Les caractères `\ / : * ? " < > |` sont refusés, car interdits dans les noms de fichiers Windows.
