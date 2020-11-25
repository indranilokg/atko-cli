import json


class Group(object):
    """Okta Group resource class.

    Holds data for an Okta group object.

    Attributes
    ----------
    _data : object
        User JSON object as returned by Okta groups API.

    Methods
    -------
    """

    def __init__(self, data=None, links=False):
        self._data = data
        self._data.pop('created', None)
        self._data.pop('lastUpdated', None)
        self._data.pop('lastMembershipUpdated', None)
        self._data.pop('objectClass', None)
        if not links:
            self._data.pop('_links', None)

    def __repr__(self):
        return json.dumps(self._data, indent=4)

    def __getitem__(self, attr):
        return self._data[attr]

    def __getattr__(self, attr):
        return self._data[attr]

    def __lt__(self, other):
        return (self._data["profile"]["name"] < other._data["profile"]["name"])

    def __eq__(self, other):
        return (self._data["id"] == other._data["id"])

    def summary(self):
        summary = [self._data["profile"]["name"],
                   self._data["profile"].get("description"),
                   self._data["type"],
                   self._data["id"]]
        return summary

    def to_dict(self):
        dictData = {}
        for attr in self._data["profile"]:
            dictData[attr] = str(self._data["profile"].get(attr, "") or "")
        dictData["id"] = self._data["id"]
        dictData["type"] = self._data["type"]
        return dictData
