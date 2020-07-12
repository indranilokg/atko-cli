import json


class User(object):
    """Okta User resource class.

    Holds data for an Okta user object.

    Attributes
    ----------
    _data : object
        User JSON object as returned by Okta user API.

    Methods
    -------
    """

    def __init__(self, data=None):
        self._data = data

    def __repr__(self):
        return json.dumps(self._data, indent=4)

    def __getitem__(self, attr):
        return self._data[attr]

    def __getattr__(self, attr):
        return self._data[attr]
