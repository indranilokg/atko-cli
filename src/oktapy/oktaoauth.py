from oktapy.exceptions import ConfigurationException, ClientException, TokenException
# from oktapy.core.api import OktaRequest
import oktapy.utils as utils
import oktapy.constants as constants

from oktapy.auth.standard import oauth


class OktaOAuth(object):
    def __init__(self, baseurl, oauthConfig=None):
        self._baseurl = baseurl
        if oauthConfig is None:
            self._oauthConfig = {constants.CONFIG_KEY_OAUTH_FLOW: "manual"}
        else:
            if not utils.validateOAuthConfigObject(oauthConfig):
                raise ConfigurationException("Unknown configuration error. Potential bug.")
            self._oauthConfig = oauthConfig
        self._tokenstore = {}
        self._oauth = oauth(self._baseurl, authServer="ORG")

    def _checkinToken(self, key, token):
        self._tokenstore[key] = token

    def _checkoutToken(self, key, skip_verification):
        token = self._tokenstore[key]
        if not skip_verification:
            self._oauth.checkTokenValidity(self._oauthConfig, token)
        return token

    def _retrieveToken(self, scopes, refesh=False):
        return self._oauth.get_token(self._oauthConfig, scopes)

    def _exchangeTokenForCode(self, code):
        return self._oauth.exchange_token_for_code(self._oauthConfig, code)

    def _exchangeTokenForRefreshToken(self, refresh_token, scopes):
        return self._oauth.exchange_token_for_refresh_token(self._oauthConfig, refresh_token, scopes)

    def _getToken(self, caller):
        token = None
        callerObjectName = caller.__class__.__name__
        if callerObjectName not in list(constants.O4O_SCOPE_MAP.keys()):
            raise ClientException(f"Caller \"{callerObjectName}\" is not a valid management resource. Supported resources are {list(constants.O4O_SCOPE_MAP.keys())}")  # noqa: E501
        if callerObjectName not in list(self._tokenstore.keys()):
            flow = self._oauthConfig[constants.CONFIG_KEY_OAUTH_FLOW]
            if flow in ['pkce', 'authorization_code', 'implicit']:
                authUrl = self.getAuthnURL(caller)
                raise TokenException("not_authenticated", f"Authenticate first with {flow} flow. Use the following URL - {authUrl}. Call the authenticate() method of the resource and seed the token", authUrl)  # noqa: E501
            elif flow in ['password', 'client_credentials']:
                if flow == 'password':
                    scopes = constants.O4O_SCOPE_MAP[callerObjectName]
                else:
                    scopes = constants.O4O_SERVICE_SCOPE_MAP[callerObjectName]
                token, refresh_token = self._retrieveToken(scopes)
                self._checkinToken(callerObjectName, token)
            else:
                raise TokenException("not_authenticated", f"Authenticate first with {flow} flow. Call the authenticate() method of the resource and seed the token")  # noqa: E501
        else:
            try:
                token = self._checkoutToken(callerObjectName, skip_verification=caller.isTokenVerified())
                caller.setTokenVerified(False)
            except TokenException as tex:
                if tex.code == "invalid_token":
                    flow = self._oauthConfig[constants.CONFIG_KEY_OAUTH_FLOW]
                    if flow in ['pkce', 'authorization_code', 'implicit']:
                        authUrl = self.getAuthnURL(caller)
                        raise TokenException("invalid_authentication", f"Try authenticating with {flow} flow. Use the following URL - {authUrl}. Call the authenticate() method of the resource and seed the token", authUrl)  # noqa: E501
                    elif flow in ['password', 'client_credentials']:
                        if flow == 'password':
                            scopes = constants.O4O_SCOPE_MAP[callerObjectName]
                        else:
                            scopes = constants.O4O_SERVICE_SCOPE_MAP[callerObjectName]
                        token, refresh_token = self._retrieveToken(scopes)
                        self._checkinToken(callerObjectName, token)
                else:
                    raise TokenException("invalid_authentication", f"Try authenticating with {flow} flow. Call the authenticate() method of the resource and seed the token")  # noqa: E501

        return token

    def authenticate(self, caller, input=None, verify=True, passive=False, refresh=False):
        callerObjectName = caller.__class__.__name__
        if callerObjectName not in list(constants.O4O_SCOPE_MAP.keys()):
            raise ClientException(f"Caller \"{callerObjectName}\" is not a valid management resource. Supported resources are {list(constants.O4O_SCOPE_MAP.keys())}")  # noqa: E501
        scopes = constants.O4O_SCOPE_MAP[callerObjectName]
        flow = self._oauthConfig[constants.CONFIG_KEY_OAUTH_FLOW]
        token = None
        refresh_token = None
        if refresh:
            token, refresh_token = self._exchangeTokenForRefreshToken(input, scopes)
        elif passive:
            token, refresh_token = self._retrieveToken(scopes)
            self.setToken(caller, token, verify=False)
        else:
            if flow in ['pkce', 'authorization_code']:
                token, refresh_token = self._exchangeTokenForCode(input)
                self.setToken(caller, token, verify=False)
            else:
                token = input
                refresh_token = ""
                self.setToken(caller, token, verify=verify)
        return token, refresh_token

    def setToken(self, caller, token, verify=False):
        if verify:
            self._oauth.checkTokenValidity(self._oauthConfig, token)
        callerObjectName = caller.__class__.__name__
        if callerObjectName not in list(constants.O4O_SCOPE_MAP.keys()):
            raise ClientException(f"Caller \"{callerObjectName}\" is not a valid management resource. Supported resources are {list(constants.O4O_SCOPE_MAP.keys())}")  # noqa: E501
        self._tokenstore[callerObjectName] = token

    def isTokenValid(self, token):
        return self._oauth.checkTokenValidity(self._oauthConfig, token, raiseError=False)

    def getAuthnURL(self, caller):
        result = None

        callerObjectName = caller.__class__.__name__
        if callerObjectName not in list(constants.O4O_SCOPE_MAP.keys()):
            raise ClientException(f"Caller \"{callerObjectName}\" is not a valid management resource. Supported resources are {list(constants.O4O_SCOPE_MAP.keys())}")  # noqa: E501
        scopes = constants.O4O_SCOPE_MAP[callerObjectName]
        result = self._oauth.authorize(self._oauthConfig, scopes)
        return result

    def request(self, apiurl, caller, mode="get", data=None):
        """Carries out and return result from the actual REST API call to supplied Okta endpoint.

        Parameters
        ----------
        apiurl : str
            Base URL of the Okta org. Example - https://example.okta.com
        caller : object
            Caller object making the API call.
        mode : str
            REST method. Allowed values are `get`, `post`, `put`, `patch` and `delete` (default is `get`).
        data : object, optional
            REST API payload (default is None).
        """

        token = self._getToken(caller)
        # print(self._tokenstore)
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
        if mode == "get":
            return self._oauth.getRequester().get(self._baseurl + apiurl, headers=headers)
        elif mode == "post":
            return self._oauth.getRequester().post(self._baseurl + apiurl, data=data, headers=headers)
        elif mode == "delete":
            return self._oauth.getRequester().delete(self._baseurl + apiurl, headers=headers)
