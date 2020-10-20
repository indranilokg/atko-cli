"""Utility module.

The module exposes the following functions:

    * encodeURLFrangment - Encode and return URL fragments
    * base64Encode - Encode and return data in Base64 format.
"""

import urllib.parse
import base64
import re
import hashlib
import os
import pandas as pd
import oktapy.constants as constants
from oktapy.exceptions import ConfigurationException
from jwcrypto.jwk import JWK
from oktapy.core.jwt import JWT


def readCSV(inputFile):
    """Read CSV data into dictionary.

    Parameters
    ----------
    inputFile : str
        Filename.
    """

    df = pd.read_csv(inputFile, index_col=False)
    data_dict = {col: df[col].squeeze().tolist() for col in df.columns}
    return data_dict


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


def encodeDict(data):
    return urllib.parse.urlencode(data)


def encodeURLFrangment(data):
    """Process and return URL fragments by quoting special characters and encoding non-ASCII text.

    Parameters
    ----------
    data : str
        URL fragment.
    """

    return urllib.parse.quote(data)


def generatePKCEcode():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return {"code_verifier": code_verifier, "code_challenge": code_challenge}


def generateClientAssertion(jwk, client_id, aud):
    key = JWK(**jwk)
    private_key = key.export_to_pem(private_key=True, password=None)
    client_assertion = JWT().getSignedJWT(privateKey=private_key, clientid=client_id, aud=aud)
    return client_assertion


def validateOAuthConfigObject(config):
    """Validate OAuth for Okta config object.

    Parameters
    ----------
    config : object
        Oauth config to be validated.
    """

    if type(config) is not dict:
        raise ConfigurationException(
            "OAuth configuration object needs to be a dictionary")
    elif constants.CONFIG_KEY_OAUTH_FLOW not in config.keys():
        raise ConfigurationException(
            "OAuth flow is missing. Pass the OAUTH_FLOW key in the configuration object")
    else:
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        if flow not in constants.OAuthConfigAllowedFlows:
            raise ConfigurationException(
                "Unknown or unsupported OAuth flow - {}. Supported flows are - {}".format(flow, constants.OAuthConfigAllowedFlows))
        else:
            requiredParams = {
                "manual": set(),
                "password": {"client_id", "client_secret", "userid", "password"},
                "client_credentials": {"client_id", "jwk"},
                "pkce": {"client_id", "redirect_uri"},
                "authorization_code": {"client_id", "client_secret", "redirect_uri"},
                "implicit": {"client_id", "redirect_uri"}
            }
            paramSet = requiredParams.get(flow)
            if paramSet <= set(config.keys()):
                return True
            else:
                raise ConfigurationException(
                    f"Error in validating parameters for {flow} flow.\nFollowing parameters are needed - {paramSet}")
