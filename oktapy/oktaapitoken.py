from oktapy.core.api import OktaRequest


class OktaAPIToken(object):
    """API Token Manager client.

    This class acts as a client leverageing Okta API token to call Okta APIs.
    Find more details on API token here - https://developer.okta.com/docs/guides/create-an-api-token/overview/

    Attributes
    ----------
    _baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
    _token : str
            Valid API token
    _requester : object
            An instance of oktapy.core.api.OktaRequest class. This object handles the actual HTTPS API call
            to Okta endpoints


    Methods
    -------
    baseUrl()
        Returns the base URL of the target Okta org

    request(apiurl, caller, mode="get", data=None)
        Carries out and return result from the actual REST API call to supplied Okta endpoint along with
        appropriate headers and data.
    """

    def __init__(self, baseurl, token=None):
        """

        Instantiates OktaAPIToken client object along with the supplied token.
        The supplied token is assumed to be active and valid. No token validation is performed.

        Parameters
        ----------
        baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
        token : str
            API token value for the org
        """

        self._baseurl = baseurl
        assert token is not None
        self._token = token
        self._requester = OktaRequest()

    def baseurl(self):
        """Returns the base URL of the target Okta org. Example - https://example.okta.com"""

        return self._baseurl

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

        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': f'SSWS {self._token}'}
        if mode == "get":
            return self._requester.get(self._baseurl + apiurl, headers=headers)
        elif mode == "post":
            return self._requester.post(self._baseurl + apiurl, data=data, headers=headers)
        elif mode == "delete":
            return self._requester.delete(self._baseurl + apiurl, headers=headers)
