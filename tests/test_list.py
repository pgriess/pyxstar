import os.path

from pixstar.api import _parse_list_response

def test_list_basic():
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
