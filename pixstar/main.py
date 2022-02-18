from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import logging
import shutil
import sys

import osxphotos

def main():
    ap = ArgumentParser()
    ap.add_argument(
        '-v', dest='verbosity', action='count', default=0,
        help='increase logging verbosity; can be used multiple times')

    args = ap.parse_args()

    logging.basicConfig(
        style='{', format='{message}', stream=sys.stderr,
        level=logging.ERROR - args.verbosity * 10)

    db_path = osxphotos.utils.get_system_library_path()
    db = osxphotos.PhotosDB(db_path)

    photos = db.photos(persons=['Ryder Griess', 'Asher Griess'])
    photos = sorted(photos, key=lambda p: p.score.overall, reverse=True)
    photos = [p for p in photos if datetime.now(tz=timezone.utc) - p.date < timedelta(days=100)]
    for p in photos[:100]:
        print(p.path)
