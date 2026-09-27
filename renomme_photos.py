#!/usr/bin/env python3
"""
Renomme les photos d'un dossier au format PREFIXE-AAAAMMJJ-NNN.EXT

- La date provient de l'EXIF (DateTimeOriginal), sinon de la date de modification du fichier.
- Le compteur NNN repart à 001 pour chaque jour, dans l'ordre chronologique des prises de vue.
- Les fichiers qui partagent le même nom de base (ex. DSC_0002.JPG + DSC_0002.NEF)
  reçoivent le même nouveau nom (seule l'extension diffère).
- Les fichiers déjà renommés avec ce préfixe sont ignorés, et le compteur
  reprend après le plus grand numéro existant pour le jour concerné.

Usage :
    python renommer_photos.py DOSSIER --prefixe N --simulation   # aperçu sans rien toucher
    python renommer_photos.py DOSSIER --prefixe N                # renommage réel
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

EXTENSIONS_DEFAUT = {".jpg", ".jpeg", ".nef", ".cr2", ".arw", ".dng", ".heic", ".png", ".tif", ".tiff"}
EXT_EXIF = {".jpg", ".jpeg", ".tif", ".tiff"}  # formats lisibles par Pillow pour l'EXIF


def date_exif(fichier: Path):
    """Retourne la date de prise de vue EXIF, ou None."""
    if not PIL_OK or fichier.suffix.lower() not in EXT_EXIF:
        return None
    try:
        with Image.open(fichier) as img:
            exif = img.getexif()
            valeur = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal, sinon DateTime
            if valeur:
                return datetime.strptime(str(valeur).strip("\x00 "), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def date_photo(fichiers):
    """Date d'un groupe de fichiers (même nom de base) : EXIF si possible, sinon mtime."""
    for f in fichiers:
        d = date_exif(f)
        if d:
            return d, "EXIF"
    return datetime.fromtimestamp(min(f.stat().st_mtime for f in fichiers)), "fichier"


def main():
    parser = argparse.ArgumentParser(description="Renomme les photos en PREFIXE-AAAAMMJJ-NNN.EXT")
    parser.add_argument("dossier", type=Path, help="Dossier contenant les photos")
    parser.add_argument("-p", "--prefixe", required=True, help="Préfixe à utiliser (ex. N)")
    parser.add_argument("-s", "--simulation", action="store_true", help="Affiche les renommages sans les effectuer")
    args = parser.parse_args()

    dossier = args.dossier
    if not dossier.is_dir():
        sys.exit(f"Erreur : {dossier} n'est pas un dossier.")
    if not PIL_OK:
        print("Attention : Pillow n'est pas installé (pip install Pillow), "
              "les dates seront prises sur les fichiers et non dans l'EXIF.\n")

    motif_deja_fait = re.compile(rf"^{re.escape(args.prefixe)}-(\d{{8}})-(\d{{3,}})$")

    # Plus grand compteur déjà utilisé par jour (fichiers déjà renommés)
    max_par_jour = defaultdict(int)
    groupes = defaultdict(list)
    for f in dossier.iterdir():
        if not f.is_file() or f.suffix.lower() not in EXTENSIONS_DEFAUT:
            continue
        m = motif_deja_fait.match(f.stem)
        if m:
            max_par_jour[m.group(1)] = max(max_par_jour[m.group(1)], int(m.group(2)))
        else:
            groupes[f.stem].append(f)

    if not groupes:
        print("Aucune photo à renommer.")
        return

    # Datation et tri chronologique (puis par nom en cas d'égalité)
    photos = []
    for stem, fichiers in groupes.items():
        d, source = date_photo(fichiers)
        photos.append((d, stem, fichiers, source))
    photos.sort(key=lambda p: (p[0], p[1]))

    # Construction du plan de renommage
    plan = []
    compteurs = dict(max_par_jour)
    for d, stem, fichiers, source in photos:
        jour = d.strftime("%Y%m%d")
        compteurs[jour] = compteurs.get(jour, 0) + 1
        nouveau_stem = f"{args.prefixe}-{jour}-{compteurs[jour]:03d}"
        for f in sorted(fichiers):
            cible = f.with_name(nouveau_stem + f.suffix.upper())
            plan.append((f, cible, d, source))

    # Vérification des conflits avant de toucher quoi que ce soit
    conflits = [c for _, c, _, _ in plan if c.exists()]
    if conflits:
        print("Abandon : les fichiers suivants existent déjà :")
        for c in conflits:
            print(f"  {c.name}")
        sys.exit(1)

    for src, cible, d, source in plan:
        print(f"{src.name:25} -> {cible.name:25} ({d:%Y-%m-%d %H:%M:%S}, date {source})")
        if not args.simulation:
            src.rename(cible)

    print(f"\n{len(plan)} fichier(s) {'à renommer (simulation)' if args.simulation else 'renommé(s)'}.")


if __name__ == "__main__":
    main()