import lxml.etree

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
