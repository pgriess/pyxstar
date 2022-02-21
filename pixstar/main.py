from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import logging
from ssl import CERT_NONE, SSLContext
import sys

import osxphotos

from .api import API


def ls(args, api):
    if not args.item:
        for a in api.albums():
            print(a.name)

        return

    for a in api.albums():
        if a.name != args.item:
            continue

        for p in api.album_photos(a):
            print(f'{p.id}\t{p.name}')

        return

    raise Exception(f'Unable to find album {args.item}')


def rm(args, api):
    for a in api.albums():
        if args.album not in [a.name, a.id]:
            continue

        for p in api.album_photos(a):
            if args.photo not in [p.name, p.id]:
                continue

            api.album_photos_delete(a, [p])
            return

        raise Exception(f'Unable to find photo {args.photo}')

    raise Exception(f'Unable to find album {args.item}')

def main():
    ap = ArgumentParser()
    ap.add_argument(
        '-k', dest='validate_https', action='store_false', default=True,
        help='disable HTTPS certificate checking')
    # TODO: Get from Keychain
    ap.add_argument('-p', dest='password', help='Pix-Star password')
    ap.add_argument(
        '-u', dest='username', help='Pix-Star username, without @mypixstar.com')
    ap.add_argument(
        '-v', dest='verbosity', action='count', default=0,
        help='increase logging verbosity; can be used multiple times')

    sp = ap.add_subparsers(dest='subcommand')

    ls_ap = sp.add_parser('ls', help='list things')
    ls_ap.add_argument(
        'item', nargs='?',
        help='album whose photos to list; if absent list albums')

    rm_ap = sp.add_parser('rm', help='remove things')
    rm_ap.add_argument('album', help='the album whose photo to remove')
    rm_ap.add_argument('photo', help='the photo to remove')

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

    if not args.username:
        sys.stderr.write('Username: ')
        args.username = input().strip()

    if not args.password:
        sys.stderr.write('Password: ')
        args.password = input().strip()

    api = API(ssl_context=ctx)
    api.login(args.username, args.password)

    if args.subcommand == 'ls':
        ls(args, api)
    elif args.subcommand == 'rm':
        rm(args, api)
    else:
        raise Exception(f'command {args.subcommand} not found')

    if False:
        db_path = osxphotos.utils.get_system_library_path()
        db = osxphotos.PhotosDB(db_path)

        photos = db.photos(persons=['Ryder Griess', 'Asher Griess'])
        photos = sorted(photos, key=lambda p: p.score.overall, reverse=True)
        photos = [p for p in photos if datetime.now(tz=timezone.utc) - p.date < timedelta(days=100)]
        for p in photos[:100]:
            print(p.path)
