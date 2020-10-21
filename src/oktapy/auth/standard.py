from oktapy.core.api import OktaRequest
from oktapy.exceptions import TokenException, AuthException, ServiceException
import oktapy.utils as utils
import oktapy.constants as constants


class oauth(object):

    def __init__(self, baseurl, authServer, authServerId=None):
        if authServer == "ORG":
            self._baseurl = baseurl
        else:
            self._baseurl = baseurl + "/oauth2/" + authServerId
        self._requester = OktaRequest()
        self._discoveryUrl = baseurl + "/.well-known/openid-configuration"
        self._authInfo = None
        self._PKCECode = None

    def _formatScopes(self, scopes):
        return " ".join(scopes)

    def _encodedScopes(self, scopes):
        return utils.encodeURLFrangment(self._formatScopes(scopes))

    def getRequester(self):
        return self._requester

    def getDiscoveryInfo(self):
        if self._authInfo is None:
            self._authInfo, ignore = self._requester.get(self._discoveryUrl)
        return self._authInfo

    def getAuthorizationUrl(self):
        return self.getDiscoveryInfo()["authorization_endpoint"]

    def getTokenUrl(self):
        return self.getDiscoveryInfo()["token_endpoint"]

    def getUserInfoUrl(self):
        return self.getDiscoveryInfo()["userinfo_endpoint"]

    def getIntrospectUrl(self):
        return self.getDiscoveryInfo()["introspection_endpoint"]

    def checkTokenValidity(self, config, token, raiseError=True, introspect=True, tokneType="access_token"):
        valid = False
        if introspect:
            result = self.introspect(config, token, tokneType)
            valid = result['active']
        else:
            valid = True
        if (not valid) and raiseError:
            raise TokenException("invalid_token", "Token is invalid", token)
        return valid

    def introspect(self, config, token, tokneType):
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'application/json'}
        data = {"token": token, "token_type_hint": tokneType}
        if flow in ["implicit", "pkce"]:
            data.update({"client_id": config[constants.CONFIG_KEY_CLIENT_ID]})
        elif flow == 'client_credentials':
            client_assertion = utils.generateClientAssertion(
                jwk=config[constants.CONFIG_KEY_JWK],
                client_id=config[constants.CONFIG_KEY_CLIENT_ID],
                aud=self.getIntrospectUrl()
            )
            data.update({
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": client_assertion}
            )
        else:
            headers.update({'authorization': 'Basic ' + utils.base64Encode(
                config[constants.CONFIG_KEY_CLIENT_ID] + ":" + config[constants.CONFIG_KEY_CLIENT_SECRET])})
        result = self._requester.post(
            self.getIntrospectUrl(), headers=headers, data=data)
        return result

    def authorize(self, config, scopes):
        returnUrl = ""
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        allowedFlows = ['pkce', 'authorization_code', 'implicit']
        if flow not in allowedFlows:
            raise AuthException(
                "unsupported_flow", f"This method does not support {flow} OAuth flow. Supported flows are - {allowedFlows}")

        if flow == "implicit":
            returnUrl = self.getAuthorizationUrl() + "?" + "response_type=token" \
                + "&scope=" + self._encodedScopes(scopes) \
                + "&" + constants.CONFIG_KEY_CLIENT_ID + "=" + config[constants.CONFIG_KEY_CLIENT_ID] \
                + "&" + constants.CONFIG_KEY_REDIRECT_URI + "=" + config[constants.CONFIG_KEY_REDIRECT_URI] \
                + "&response_mode=form_post" \
                + "&state=oktapystate" \
                + "&nonce=random"
        elif flow == "pkce":
            self._PKCECode = utils.generatePKCEcode()
            returnUrl = self.getAuthorizationUrl() + "?" + "response_type=code" \
                + "&scope=" + self._encodedScopes(scopes) \
                + "&" + constants.CONFIG_KEY_CLIENT_ID + "=" + config[constants.CONFIG_KEY_CLIENT_ID] \
                + "&" + constants.CONFIG_KEY_REDIRECT_URI + "=" + config[constants.CONFIG_KEY_REDIRECT_URI] \
                + "&code_challenge_method=S256" \
                + "&code_challenge=" + self._PKCECode["code_challenge"] \
                + "&state=oktapystate" \
                + "&nonce=random"
        else:
            scopes = scopes + ['offline_access']
            returnUrl = self.getAuthorizationUrl() + "?" + "response_type=code" \
                + "&scope=" + self._encodedScopes(scopes) \
                + "&" + constants.CONFIG_KEY_CLIENT_ID + "=" + config[constants.CONFIG_KEY_CLIENT_ID] \
                + "&" + constants.CONFIG_KEY_REDIRECT_URI + "=" + config[constants.CONFIG_KEY_REDIRECT_URI] \
                + "&state=oktapystate" \
                + "&nonce=random"
        print(returnUrl)
        return returnUrl

    def get_token(self, config, scopes):
        access_token = None
        refresh_token = None
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        allowedFlows = ['password', 'client_credentials']
        if flow not in allowedFlows:
            raise AuthException(
                "unsupported_flow", f"This method does not support {flow} OAuth flow. Supported flows are - {allowedFlows}")

        if flow == "password":
            scopes = scopes + ['offline_access']
            _base64_encoded_credentials = utils.base64Encode(config[constants.CONFIG_KEY_CLIENT_ID] + ":" + config[constants.CONFIG_KEY_CLIENT_SECRET])
            headers = {'authorization': 'Basic ' + _base64_encoded_credentials,
                       'Content-Type': 'application/x-www-form-urlencoded',
                       'Accept': 'application/json'}
            data = {"grant_type": "password", "scope": self._formatScopes(
                scopes), "username": config[constants.CONFIG_KEY_USER_ID], "password": config[constants.CONFIG_KEY_USER_PWD]}
        else:
            headers = {'Content-Type': 'application/x-www-form-urlencoded',
                       'Accept': 'application/json'}
            client_assertion = utils.generateClientAssertion(
                jwk=config[constants.CONFIG_KEY_JWK],
                client_id=config[constants.CONFIG_KEY_CLIENT_ID],
                aud=self.getTokenUrl()
            )
            data = {"grant_type": "client_credentials", "scope": self._formatScopes(scopes),
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion}

        payload = utils.encodeDict(data)
        result = self._requester.post(
            self.getTokenUrl(), headers=headers, data=payload)
        access_token, refresh_token = result["access_token"], result.get(
            "refresh_token", "")
        return access_token, refresh_token

    def exchange_token_for_code(self, config, code):
        access_token = None
        refresh_token = None
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        allowedFlows = ['authorization_code', 'pkce']
        if flow not in allowedFlows:
            raise AuthException(
                "unsupported_flow", f"This method does not support {flow} OAuth flow. Supported flow is - {allowedFlows}")

        if flow == "pkce":
            headers = {'Content-Type': 'application/x-www-form-urlencoded',
                       'Accept': 'application/json'}
            data = {"grant_type": "authorization_code", "code": code,
                    "redirect_uri": config[constants.CONFIG_KEY_REDIRECT_URI],
                    "client_id": config[constants.CONFIG_KEY_CLIENT_ID],
                    "code_verifier": self._PKCECode["code_verifier"]}
        else:
            _base64_encoded_credentials = utils.base64Encode(config[constants.CONFIG_KEY_CLIENT_ID] + ":" + config[constants.CONFIG_KEY_CLIENT_SECRET])
            headers = {'authorization': 'Basic ' + _base64_encoded_credentials,
                       'Content-Type': 'application/x-www-form-urlencoded',
                       'Accept': 'application/json'}
            data = {"grant_type": "authorization_code", "code": code,
                    "redirect_uri": config[constants.CONFIG_KEY_REDIRECT_URI]}

        payload = utils.encodeDict(data)
        result = self._requester.post(
            self.getTokenUrl(), headers=headers, data=payload)
        access_token, refresh_token = result["access_token"], result.get(
            "refresh_token", "")
        return access_token, refresh_token

    def exchange_token_for_refresh_token(self, config, refresh_token, scopes):
        scopes = scopes + ['offline_access']
        access_token = None
        new_refresh_token = None
        flow = config[constants.CONFIG_KEY_OAUTH_FLOW]
        allowedFlows = ['authorization_code', 'password']
        if flow not in allowedFlows:
            raise AuthException(
                "unsupported_flow", f"This method does not support {flow} OAuth flow. Supported flow is - {allowedFlows}")

        headers = {'authorization': 'Basic ' + utils.base64Encode(config[constants.CONFIG_KEY_CLIENT_ID] + ":" + config[constants.CONFIG_KEY_CLIENT_SECRET]),
                   'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token,
                "redirect_uri": config[constants.CONFIG_KEY_REDIRECT_URI], "scope": self._formatScopes(scopes)}

        payload = utils.encodeDict(data)
        try:
            result = self._requester.post(
                self.getTokenUrl(), headers=headers, data=payload)
        except ServiceException:
            raise
        except Exception:
            raise
        access_token, new_refresh_token = result["access_token"], result.get(
            "refresh_token", "")
        return access_token, new_refresh_token
