"""Utility module.

The module exposes the following functions:

    * encodeURLFrangment - Encode and return URL fragments
    * base64Encode - Encode and return data in Base64 format.
"""

import urllib.parse
import base64
# from jwcrypto.jwk import JWK
# from oktapy.core.jwt import JWT

"""
def encodeDict(data):
    return urllib.parse.urlencode(data)
"""


def encodeURLFrangment(data):
    """Process and return URL fragments by quoting special characters and encoding non-ASCII text.

    Parameters
    ----------
    data : str
        URL fragment.
    """

    return urllib.parse.quote(data)


def base64Encode(data):
    """Encode and return data in Base64 format.

    Parameters
    ----------
    data : str
        data to be encoded.
    """

    encodedBytes = base64.b64encode(data.encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    return encodedStr
