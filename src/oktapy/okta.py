from oktapy.oktaapitoken import OktaAPIToken

from oktapy.exceptions import ConfigurationException
from oktapy.manage.UserMgr import UserMgr
from oktapy.manage.GroupMgr import GroupMgr


class Okta(object):
    """Top level Okta resource management class.

    This is the top level class that provides API interface to manage Okta resources.
    It uses API token mode for authentication.

    Attributes
    ----------
    _baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
    _client : object
            Associated Okta client object. Instance of OktaAPIToken class.

    Methods
    -------
    client()
        Returns the associated Okta client object

    baseUrl()
        Returns the base URL of the target Okta org

    UserMgr()
        Instantiates and returns Okta user manager object

    GroupMgr()
        Instantiates and returns Okta group manager object
    """

    def __init__(self, baseurl, token=None, verbose=False):
        """
        Instantiates and associates an OktaAPIToken client object.

        Parameters
        ----------
        baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
        token : str
            API token value for the org.
        verbose : bool
            Flag to enable verbose API calls
        """
        self._baseurl = baseurl
        self._token = token
        self._verbose = verbose
        self._client = OktaAPIToken(baseurl, token=token, verbose=verbose)

    def client(self):
        """Returns the associated OktaAPIToken client object."""
        return self._client

    def baseUrl(self):
        """Returns the base URL of the target Okta org. Example - https://example.okta.com"""
        return self._baseurl

    def UserMgr(self):
        """Instantiates and returns Okta user manager object.

        User manager is responsible for managing user specific operations.
        """
        return UserMgr(client=self._client)

    def GroupMgr(self):
        """Instantiates and returns Okta group manager object.

        Group manager is responsible for managing group specific operations.
        """
        return GroupMgr(client=self._client)
