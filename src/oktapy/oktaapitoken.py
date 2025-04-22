from oktapy.core.api import OktaRequest
import click
import json


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
    _verbose : bool
            Flag to print API calls as cURL commands


    Methods
    -------
    baseUrl()
        Returns the base URL of the target Okta org

    request(apiurl, caller, mode="get", data=None)
        Carries out and return result from the actual REST API call to supplied Okta endpoint along with
        appropriate headers and data.
    """

    def __init__(self, baseurl, token=None, verbose=False):
        """

        Instantiates OktaAPIToken client object along with the supplied token.
        The supplied token is assumed to be active and valid. No token validation is performed.

        Parameters
        ----------
        baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
        token : str
            API token value for the org
        verbose : bool
            Flag to print API calls as cURL commands
        """

        self._baseurl = baseurl
        assert token is not None
        self._token = token
        self._verbose = verbose
        self._requester = OktaRequest()

    def baseurl(self):
        """Returns the base URL of the target Okta org. Example - https://example.okta.com"""

        return self._baseurl

    def _print_curl(self, url, mode, headers, data=None):
        if not self._verbose:
            return
            
        # Start building curl command
        curl_cmd = ['curl']
        
        # Add method if not GET
        if mode.upper() != 'GET':
            curl_cmd.append(f'-X {mode.upper()}')
        
        # Add headers
        for key, value in headers.items():
            if key == 'Authorization':
                # Mask the token
                curl_cmd.append(f"-H '{key}: SSWS ***'")
            else:
                curl_cmd.append(f"-H '{key}: {value}'")
        
        # Add data if present
        if data:
            curl_cmd.append(f"-d '{data}'")
        
        # Add URL
        curl_cmd.append(f"'{url}'")
        
        # Print the command
        click.echo("\nAPI Call:")
        click.echo(" ".join(curl_cmd))
        click.echo()

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
        
        full_url = self._baseurl + apiurl
        self._print_curl(full_url, mode, headers, data)

        if mode == "get":
            return self._requester.get(full_url, headers=headers)
        elif mode == "post":
            return self._requester.post(full_url, data=data, headers=headers)
        elif mode == "put":
            return self._requester.put(full_url, data=data, headers=headers)
        elif mode == "delete":
            return self._requester.delete(full_url, headers=headers)
