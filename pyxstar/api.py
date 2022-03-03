from collections import namedtuple
from http.cookiejar import CookieJar
import lxml.etree
import random
import re
from string import ascii_lowercase
import time
from urllib.parse import urlencode
import urllib.request


Album = namedtuple('Album', ['id', 'name'])
Photo = namedtuple('Photo', ['id', 'name'])


class API:
    cookie_jar = None
    csrf_token = None
    url_opener = None

    def __init__(self, ssl_context=None):
        self.cookie_jar = CookieJar()
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=ssl_context))

    def login(self, username, password):
        '''
        Login to the Pix-Star service.

        This method must be invoked before any other methods.
        '''

        assert not self.csrf_token

        self.url_opener.open('https://www.pix-star.com/')
        for c in self.cookie_jar:
            if c.name == 'csrftoken':
                self.csrf_token = c.value

        assert self.csrf_token

        resp = self.url_opener.open(
            'https://www.pix-star.com/accounts/login/',
            data=urlencode({
                'csrfmiddlewaretoken': self.csrf_token,
                'username': username,
                'password': password}).encode('utf-8'))

        assert resp.status == 200
        assert resp.geturl() == 'https://www.pix-star.com/my_pixstar/'

    # TODO: Handle paging
    def albums(self):
        '''
        List the user's web albums.
        '''

        assert self.csrf_token

        resp = self.url_opener.open('https://www.pix-star.com/albums/list/')
        assert resp.status == 200

        return _parse_list_response(resp)

    def album(self, name):
        '''
        Get an album with a specific name. Raises a KeyError if the album could
        not be found.
        '''

        assert self.csrf_token

        for a in self.albums():
            if a.name == name:
                return a

        raise KeyError()

    # TODO: How does the server handle duplicate album names? The UI pops up an alert
    #       but doesn't actually make the request
    def album_create(self, name):
        '''
        Create the given album, returning it.
        '''

        qs = urlencode({
            'album_name': name,
            'csrfmiddlewaretoken': self.csrf_token,
        })
        resp = self.url_opener.open(
            f'https://www.pix-star.com/create/new_album/?{qs}')

        assert resp.status == 200
        m = re.match(r'^https://www.pix-star.com/album/web/([0-9]+)/', resp.geturl())
        assert m
        album_id = m.group(1)

        for a in self.albums():
            if a.id == album_id:
                return a

        raise Exception('Could not find newly-created album')

    def album_delete(self, albums):
        '''
        Delete several albums.
        '''

        # TODO: Paging of delete requests
        req = urllib.request.Request(
            f'https://www.pix-star.com/delete/album/',
            data=urlencode(
                [('web_albums[]', a.id) for a in albums]).encode('utf-8'))
        req.add_header('X-Requested-With', 'XMLHttpRequest')

        resp = self.url_opener.open(req)
        assert resp.status == 200

    def album_photos(self, album):
        '''
        Get information about the given album.
        '''

        assert self.csrf_token

        photos = []
        page_num = 1
        while True:
            qs = urlencode({
                'page': page_num,
                'size': 'small',
                '_': int(time.time() * 1000),
            })
            req = urllib.request.Request(f'https://www.pix-star.com/album/web/{album.id}/?{qs}')
            # XXX: Without this X-Requested-With header, we get a 404 on the last page
            #      rather than the sentintel 'no-more' response. The Pix-Star website
            #      uses the sentinel response, so do the same here.
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            resp = self.url_opener.open(req)
            assert resp.status == 200

            page_photos = _parse_album_photos_response(resp)
            if not page_photos:
                return photos

            photos += page_photos
            page_num += 1

    def album_photo_upload(self, album, f, name, mime_type):
        '''
        Upload a photo to an album.
        '''

        mime_boundary = '----pyxstar'
        mime_boundary += ''.join(random.choices(ascii_lowercase, k=16))

        body = bytearray()
        body += '\r\n'.join([
            ('--' + mime_boundary),
            f'Content-Disposition: form-data; name="image"; filename="{name}"',
            f'Content-Type: {mime_type}',
            '',
            '']).encode('utf-8')
        body += f.read() + b'\r\n'
        body += ('--' + mime_boundary + '--').encode('utf-8') + b'\r\n'

        qs = urlencode({'size': 'small'})
        req = urllib.request.Request(
            f'https://www.pix-star.com/album/web/{album.id}/?{qs}',
            data=body)
        req.add_header('Content-Type', 'multipart/form-data; boundary=' + mime_boundary)
        req.add_header('X-Requested-With', 'XMLHttpRequest')

        resp = self.url_opener.open(req)
        assert resp.status == 200

    def album_photos_delete(self, album, photos):
        '''
        Delete photos from the given album.
        '''

        # TODO: Paging of delete requests
        req = urllib.request.Request(
            f'https://www.pix-star.com/delete/album/image/',
            data=urlencode(
                [('images[]', p.id) for p in photos] +
                [
                    ('album_id', album.id),
                    ('size', 'small'),
                    ('album_type', 'web')]).encode('utf-8'))
        req.add_header('X-Requested-With', 'XMLHttpRequest')

        resp = self.url_opener.open(req)
        assert resp.status == 200


def _parse_list_response(f):
    albums = []

    doc = lxml.etree.parse(f, lxml.etree.HTMLParser())

    # TODO: Use CSS selectors which will handle attributes better, e.g. not requiring
    #       a full class match. See https://lxml.de/apidoc/lxml.cssselect.html.
    for a in doc.xpath('//a[@class="album_title"]'):
        parent = a.getparent()
        assert parent.tag == 'div'

        id = parent.attrib['id']
        assert id.startswith('album_id_')
        id = id[len('album_id_'):]

        albums.append(Album(id=id, name=a.text))

    return albums


def _parse_album_photos_response(f):
    photos = []

    # There are some sentinel values that the "API" returns -- 'no-data' for a
    # read past the last page of results, and '\n\n' when the album is
    # completely empty.
    data = f.read().strip()
    if not data or data == 'no-more':
        return photos

    doc = lxml.etree.fromstring(data, lxml.etree.HTMLParser())

    for li in doc.xpath('//li[@class="album-image"]'):
        cb = li.xpath('.//input[@type="checkbox"][@class="image-checkbox"]')
        assert len(cb) == 1

        a = li.xpath('.//h5[@class="photo_title"]')
        assert len(a) == 1

        photos.append(
            Photo(
                id=cb[0].attrib['value'],
                name=a[0].attrib['title']))

    return photos
