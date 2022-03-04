from argparse import ArgumentParser, Namespace
import logging
import mimetypes
import os.path
from ssl import CERT_NONE, SSLContext
import sys

from .api import API


def ls(args: Namespace, api: API) -> None:
    if not args.item:
        for a in api.albums():
            print(a.name)

        return

    for a in api.albums():
        if a.name != args.item:
            continue

        for p in api.album_photos(a):
            print(f"{p.id}\t{p.name}")

        return

    raise Exception(f"Unable to find album {args.item}")


def rm(args: Namespace, api: API) -> None:
    for a in api.albums():
        if args.album not in [a.name, a.id]:
            continue

        for p in api.album_photos(a):
            if args.photo not in [p.name, p.id]:
                continue

            api.album_photos_delete(a, [p])
            return

        raise Exception(f"Unable to find photo {args.photo}")

    raise Exception(f"Unable to find album {args.item}")


def upload(args: Namespace, api: API) -> None:
    # TODO: Use API.album(); extend to support lookup by ID
    album = None
    for a in api.albums():
        if args.album in [a.name, a.id]:
            album = a
            break

    assert album

    mime_type = mimetypes.guess_type(args.path)[0]
    assert mime_type

    with open(args.path, "rb") as f:
        api.album_photo_upload(
            album, f, name=os.path.basename(args.path), mime_type=mime_type
        )


def main():
    ap = ArgumentParser()
    ap.add_argument(
        "-k",
        dest="validate_https",
        action="store_false",
        default=True,
        help="disable HTTPS certificate checking",
    )
    # TODO: Get from Keychain
    ap.add_argument("-p", dest="password", help="Pix-Star password")
    ap.add_argument(
        "-u", dest="username", help="Pix-Star username, without @mypixstar.com"
    )
    ap.add_argument(
        "-v",
        dest="verbosity",
        action="count",
        default=0,
        help="increase logging verbosity; can be used multiple times",
    )

    sp = ap.add_subparsers(dest="subcommand")

    sp.add_parser("help", help="show help")

    ls_ap = sp.add_parser("ls", help="list things")
    ls_ap.add_argument(
        "item", nargs="?", help="album whose photos to list; if absent list albums"
    )

    rm_ap = sp.add_parser("rm", help="remove things")
    rm_ap.add_argument("album", help="the album whose photo to remove")
    rm_ap.add_argument("photo", help="the photo to remove")

    upload_ap = sp.add_parser("upload", help="upload a file")
    upload_ap.add_argument("album", help="album to upload the photo to")
    upload_ap.add_argument("path", help="path to the file to upload")

    args = ap.parse_args()

    if args.subcommand in ["help", None]:
        ap.print_help()
        sys.exit(0)

    logging.basicConfig(
        style="{",
        format="{message}",
        stream=sys.stderr,
        level=logging.ERROR - args.verbosity * 10,
    )

    ctx = None
    if not args.validate_https:
        ctx = SSLContext()
        ctx.verify_mode = CERT_NONE

    if not args.username:
        sys.stderr.write("Username: ")
        args.username = input().strip()

    if not args.password:
        sys.stderr.write("Password: ")
        args.password = input().strip()

    api = API(ssl_context=ctx)
    api.login(args.username, args.password)

    if args.subcommand == "ls":
        ls(args, api)
    elif args.subcommand == "rm":
        rm(args, api)
    elif args.subcommand == "upload":
        upload(args, api)
    else:
        raise Exception(f"command {args.subcommand} not found")
