from http.cookiejar import CookieJar
import logging
import lxml.etree
import time
from urllib.parse import urlencode
import urllib.request


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

    def album_photos(self, album_id):
        '''
        Get information about the given album.
        '''

        assert self.csrf_token

        photos = set()
        page_num = 1
        while True:
            logging.info(f'Requesting page {page_num}')

            qs = urlencode({
                'page': page_num,
                'size': 'small',
                '_': int(time.time() * 1000),
            })
            req = urllib.request.Request(f'https://www.pix-star.com/album/web/{album_id}/?{qs}')
            # XXX: Without this X-Requested-With header, we get a 404 on the last page
            #      rather than the sentintel 'no-more' response. The Pix-Star website
            #      uses the sentinel response, so do the same here.
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            resp = self.url_opener.open(req)
            assert resp.status == 200

            page_photos = _parse_album_photos_response(resp)
            if not page_photos:
                return photos

            photos |= page_photos
            page_num += 1


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

        albums.append({
            'name': a.text,
            'id': id,
        })

    return albums


def _parse_album_photos_response(f):
    photos = []

    data = f.read()
    if data == 'no-more':
        return photos

    doc = lxml.etree.fromstring(data, lxml.etree.HTMLParser())

    for li in doc.xpath('//li[@class="album-image"]'):
        cb = li.xpath('.//input[@type="checkbox"][@class="image-checkbox"]')
        assert len(cb) == 1

        a = li.xpath('.//h5[@class="photo_title"]')
        assert len(a) == 1

        photos.append({
            'title': a[0].attrib['title'],
            'id': cb[0].attrib['value'],
        })

    return photos
