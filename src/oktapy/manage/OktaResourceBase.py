class OktaResourceBase(object):
    """Parent class for Okta resource manager.

    This is the parent class for various Okta resource managers. Resources could be -
    users, groups, policies, authorization servers, and so on.
    All resource managers inherit from this class.

    Attributes
    ----------
    _client : object
        Associated Okta client object. Can be an instance of OktaAPIToken or OktaOAuth class.

    Methods
    -------
    """

    def __init__(self, client):
        """

        Instantiates an Okta resource manager object.

        Parameters
        ----------
        client : object
            Okta client object to associate. Can be an instance of OktaAPIToken or OktaOAuth class.
        """
        self._client = client
        self._tokenVerified = False

    def initAuth(self):
        return self._client.getAuthnURL(self)

    def authenticate(self, input=None, passive=False, verify=True):
        return self._client.authenticate(self, input=input, verify=verify, passive=passive)

    def generateNewToken(self, refresh_token):
        return self._client.authenticate(self, input=refresh_token, verify=False, refresh=True)

    def setToken(self, token, verify=True):
        self._client.setToken(self, token, verify=verify)

    def isTokenValid(self, token):
        return self._client.isTokenValid(token)

    def isTokenVerified(self):
        return self._verified

    def setTokenVerified(self, flg):
        self._verified = flg
