import configparser
import os.path
import random
import re
from string import ascii_lowercase

import pytest

from pyxstar.api import Album, API, Photo


@pytest.fixture
def api() -> API:
    '''
    Fixture to provide a logged-in API object.
    '''

    cp = configparser.ConfigParser()
    cp.read(os.path.join(os.path.dirname(__file__), 'data', 'pyxstar.ini'))

    a = API()
    a.login(cp['Test']['username'], cp['Test']['password'])

    return a


def test_integration(api: API) -> None:
    '''
    An integration test.
    '''

    # Create an album for testing
    album_name = 'test_' + ''.join(random.choices(ascii_lowercase, k=12))
    album = api.album_create(album_name)

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

    # Delete the album
    api.album_delete([album])

    # It should no longer be visible via the list from albums()
    assert [] == [a for a in api.albums() if a.id == album.id]

    # It should no longer be visible via album()
    with pytest.raises(KeyError):
        api.album(album_name)
