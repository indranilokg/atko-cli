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

    def __init__(self, data=None, links=False, attr=None):
        self._data = data
        if attr is not None:
            filteredData = {}
            attrList = attr.split(",")
            attrList = list(set(attrList) - {"id", "login", "status"})
            profile = {"login": self._data["profile"]["login"]}
            for attr in attrList:
                if attr in self._data["profile"]:
                    profile[attr] = self._data["profile"].get(attr, "")
            filteredData["id"] = self._data["id"]
            filteredData["status"] = self._data["status"]
            filteredData["profile"] = profile
            self._data = filteredData
        elif not links:
            self._data.pop('_links', None)

    def __repr__(self):
        return json.dumps(self._data, indent=4)

    def __getitem__(self, attr):
        return self._data[attr]

    def __getattr__(self, attr):
        return self._data[attr]

    def __lt__(self, other):
        return (self._data["profile"]["login"] < other._data["profile"]["login"])

    def __eq__(self, other):
        return (self._data["id"] == other._data["id"])

    def summary(self):
        summary = [self._data["profile"]["login"],
                   self._data["profile"].get("firstName"),
                   self._data["profile"].get("lastName"),
                   self._data["profile"].get("email"),
                   self._data["status"],
                   self._data["id"]]
        return summary

    def to_dict(self):
        dictData = {}
        for attr in self._data["profile"]:
            dictData[attr] = str(self._data["profile"].get(attr, "") or "")
        dictData["id"] = self._data["id"]
        dictData["status"] = self._data["status"]
        return dictData
