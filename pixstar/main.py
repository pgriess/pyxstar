from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import logging
from ssl import CERT_NONE, SSLContext
import sys

import osxphotos

from .api import API


def main():
    ap = ArgumentParser()
    ap.add_argument(
        '-v', dest='verbosity', action='count', default=0,
        help='increase logging verbosity; can be used multiple times')
    ap.add_argument(
        '-k', dest='validate_https', action='store_false', default=True,
        help='disable HTTPS certificate checking')
    ap.add_argument(
        'username', help='Pix-Start username, without @mypixstar.com')
    # TODO: Get from Keychain
    ap.add_argument(
        'password', help='Pix-Star password')

    args = ap.parse_args()

    # TODO: Something is changing our logging config before we get a chance to
    #       run? The format that we're seeing is different than expected.
    logging.basicConfig(
        style='{', format='{message}', stream=sys.stderr,
        level=logging.ERROR - args.verbosity * 10)

    ctx = None
    if not args.validate_https:
        ctx = SSLContext()
        ctx.verify_mode = CERT_NONE

    api = API(ssl_context=ctx)
    api.login(args.username, args.password)

    for a in api.albums():
        api.album_photos_delete(a, api.album_photos(a)[:2])

    if False:
        db_path = osxphotos.utils.get_system_library_path()
        db = osxphotos.PhotosDB(db_path)

        photos = db.photos(persons=['Ryder Griess', 'Asher Griess'])
        photos = sorted(photos, key=lambda p: p.score.overall, reverse=True)
        photos = [p for p in photos if datetime.now(tz=timezone.utc) - p.date < timedelta(days=100)]
        for p in photos[:100]:
            print(p.path)
