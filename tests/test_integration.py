import configparser
import os.path
import re

import pytest

from pyxstar.api import Album, API, Photo


@pytest.fixture
def api():
    '''
    Fixture to provide a logged-in API object.
    '''

    cp = configparser.ConfigParser()
    cp.read(os.path.join(os.path.dirname(__file__), 'data', 'pyxstar.ini'))

    a = API()
    a.login(cp['Test']['username'], cp['Test']['password'])

    return a


def test_integration(api):
    '''
    An integration test.
    '''

    # We should have at one album for testing
    albums = [a for a in api.albums() if re.match(r'^test_', a.name, re.I)]
    assert albums == [Album(name='Test_Integration', id='4345266')]
    album = albums[0]

    assert len(api.album_photos(album)) == 0

    # Upload a photo
    with open(
            os.path.join(
                os.path.dirname(__file__), 'data', '2594247316_b8a918ffa8_b.jpg'),
            'rb') as f:
        api.album_photo_upload(album, f, 'foo.jpg', 'image/jpeg')

    # It should show up in the photo list
    album_photos = api.album_photos(album)
    assert len(album_photos) == 1

    # Delete the photo
    api.album_photos_delete(album, album_photos)

    # It should be gone from the list
    assert len(api.album_photos(album)) == 0
