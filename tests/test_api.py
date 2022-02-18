import os.path

from pixstar.api import _parse_list_response, _parse_album_photos_response

def test_albums():
    '''
    Verify parsing of the /albums/list endpoint.
    '''

    with open(
            os.path.join(
                os.path.dirname(__file__),
                'data',
                'albums_list.html'),
            'r',
            encoding='utf-8') as f:
        assert _parse_list_response(f) == [
            {'name': 'Test Album', 'id': '4342523'}]


def test_album_photos():
    '''
    Verify basic parsing of the /album/web/<id> endpoint.
    '''

    with open(
            os.path.join(
                os.path.dirname(__file__),
                'data',
                'album_web.html'),
            'r',
            encoding='utf-8') as f:
        assert _parse_album_photos_response(f) == {
            'final_dsc1458_122.jpg',
            '_dsc1614_121.jpg',
            '_dsc1613_120.jpg',
            '_dsc1610_119.jpg'}


def test_album_photos():
    '''
    Verify parsing of end-of-list response from the /album/web/<id> endpoint.
    '''

    with open(
            os.path.join(
                os.path.dirname(__file__),
                'data',
                'album_web_end.html'),
            'r',
            encoding='utf-8') as f:
        assert _parse_album_photos_response(f) == set()
