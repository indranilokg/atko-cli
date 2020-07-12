from oktapy.oktaapitoken import OktaAPIToken

from oktapy.exceptions import ConfigurationException
from oktapy.manage.UserMgr import UserMgr


class Okta(object):
    """Top level Okta resource management class.

    This is the top level class that provides API intereface to manage Okta resources.
    It supports API token or OAuth for Okta modes. Default is API token mode.

    Attributes
    ----------
    _baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
    _client : object
            Associated Okta client object. Can be an instance of OktaAPIToken or OktaOAuth class.

    Methods
    -------
    client()
        Returns the associated Okta client object

    baseUrl()
        Returns the base URL of the target Okta org

    UserMgr()
        Instantiates and returns Okta user manager object
    """

    def __init__(self, baseurl, mode='apitoken', token=None, oauthConfig=None):
        """

        Instantiates and associates appropriate Okta client object based on the mode.
        If the mode is `apioken` associates an OktaAPIToken object. If the mode is `oauth`
        then an OktaOAuth client object is associated.

        Parameters
        ----------
        baseurl : str
            Base URL of the Okta org. Example - https://example.okta.com
        mode : str
            Management modes. Allowed value - `apitoken`, `oauth` (default is `apitoken`).
        token : str
            API token value for the org. Manadatory if the mode is `apitoken` (default is None).
        oauthConfig : object
            OAuth for Okta configuration information. Manadatory if the mode is `oauth` (default is None).

        Raises
        ------
        ConfigurationException
            If invalid mode is passed. Valid values are - `apitoken`, `oauth`
        """

        self._baseurl = baseurl
        if mode == 'apitoken':
            self._client = OktaAPIToken(baseurl, token)
        else:
            raise ConfigurationException(f"{mode}: Unsupported SDK mode. Supported modes are - apitoken, oauth")

    def client(self):
        """Returns the associated Okta client object.

        If the mode is `apitoken` returns the associated OktaAPIToken object.
        If the mode is 'oauth` then the associated OktaOAuth client object is returned.
        """

        return self._client

    def baseUrl(self):
        """Returns the base URL of the target Okta org. Example - https://example.okta.com"""

        return self._baseurl

    def UserMgr(self):
        """Instantiates and returns Okta user manager object.

        User manager is responsible for managing user specific operations.
        """

        return UserMgr(client=self._client)
