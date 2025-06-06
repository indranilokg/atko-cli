class OktaResourceBase(object):
    """Parent class for Okta resource manager.

    This is the parent class for various Okta resource managers. Resources could be -
    users, groups, policies, authorization servers, and so on.
    All resource managers inherit from this class.

    Attributes
    ----------
    _client : object
        Associated Okta client object. Instance of OktaAPIToken class.
    """

    def __init__(self, client):
        """
        Instantiates an Okta resource manager object.

        Parameters
        ----------
        client : object
            Okta client object to associate. Instance of OktaAPIToken class.
        """
        self._client = client 