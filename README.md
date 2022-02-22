A Python library and commandline tool for managing [Pix-Star](https://www.pix-star.com/) digital photo frames.

# Installation

You can install from PyPI using `pip` as follows

```bash
pip install pyxstar
```

# Usage

## Python library

The `pyxstar.api` module is the basis for all API interactions with the Pix-Star service. The `API` class should be used to invoke methods on the service, which accept and return `Album` and `Photo` classes.

For example

```python
from pyxstar.api import API

api = API()
api.login('myusername', 'mypassword')
for a in api.albums():
    print(f'Album: {a.name}')

    for p in api.album_photos(a):
        print(f'  Photo: {p.name}')
```

## Commandline

This package provides a `pyxstar` commandline tool which offers a variety of subcommands to interact with your digital photo frame.

The following are some examples of how to use this:

```bash
# Show help
$ pyxstar help
[...]

# List album names
$ pyxstar -u myusername -p mypassword ls
My First Album
My Second Album

# List photos in My First Album
$ pyxstar -u myusername -p mypassword ls 'My First Album'
315371094   _dsc1254_59.jpg
315371095   _dsc1254_60.jpg

# Upload a photo to My First Album and check that it exists
$ pyxstar -u myusername -p mypassword upload 'My First Album' /path/to/foo.jpg
$ pyxstar -u myusername -p mypassword ls 'My First Album'
315371094   _dsc1254_59.jpg
315371095   _dsc1254_60.jpg
315371099   foo.jpg
```
