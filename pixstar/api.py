from http.cookiejar import CookieJar
import lxml.etree
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
            data=urllib.parse.urlencode({
                'csrfmiddlewaretoken': self.csrf_token,
                'username': username,
                'password': password}).encode('utf-8'))

        assert resp.status == 200
        assert resp.geturl() == 'https://www.pix-star.com/my_pixstar/'

    def albums(self):
        '''
        List the user's web albums.
        '''

        assert self.csrf_token

        resp = self.url_opener.open('https://www.pix-star.com/albums/list/')
        assert resp.status == 200

        return _parse_list_response(resp)


def _parse_list_response(f):
    '''
    Parse the HTML from an /albums/list/ response.
    '''

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

        name = a.text
        albums.append({
            'name': a.text,
            'id': id,
        })

    return albums
