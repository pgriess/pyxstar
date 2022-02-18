from argparse import ArgumentParser
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from http.cookiejar import CookieJar
import logging
import lxml.etree
from ssl import CERT_NONE, SSLContext
import sys
from urllib.parse import urlencode
import urllib.request

import osxphotos
from parso import parse


class HTTPNoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        return None


def main():
    ap = ArgumentParser()
    ap.add_argument(
        '-v', dest='verbosity', action='count', default=0,
        help='increase logging verbosity; can be used multiple times')
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

    ctx = SSLContext()
    ctx.verify_mode = CERT_NONE

    cj = CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ctx))
    opener.open('https://www.pix-star.com/')
    csrftoken = None
    for c in cj:
        if c.name == 'csrftoken':
            csrftoken = c.value

    assert csrftoken
    logging.info(f'Found CSRF token: {csrftoken}')

    resp = opener.open(
        'https://www.pix-star.com/accounts/login/',
        data=urllib.parse.urlencode({
            'csrfmiddlewaretoken': csrftoken,
            'username': args.username,
            'password': args.password}).encode('utf-8'))

    assert resp.status == 200
    assert resp.geturl() == 'https://www.pix-star.com/my_pixstar/'

    logging.info('Logged in')

    resp = opener.open('https://www.pix-star.com/albums/list/')
    assert resp.status == 200

    doc = lxml.etree.parse(resp, lxml.etree.HTMLParser())

    if False:
        db_path = osxphotos.utils.get_system_library_path()
        db = osxphotos.PhotosDB(db_path)

        photos = db.photos(persons=['Ryder Griess', 'Asher Griess'])
        photos = sorted(photos, key=lambda p: p.score.overall, reverse=True)
        photos = [p for p in photos if datetime.now(tz=timezone.utc) - p.date < timedelta(days=100)]
        for p in photos[:100]:
            print(p.path)
