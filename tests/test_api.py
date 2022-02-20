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
        assert _parse_album_photos_response(f) == [
            {'title': 'final_dsc1458_122.jpg', 'id': '335372090'},
            {'title': '_dsc1614_121.jpg', 'id': '335372089'},
            {'title': '_dsc1613_120.jpg', 'id': '335372088'},
            {'title': '_dsc1610_119.jpg', 'id': '335372087'},
        ]


def test_album_photos_end():
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
        assert _parse_album_photos_response(f) == []
