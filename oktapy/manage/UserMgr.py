from oktapy.manage.OktaResourceBase import OktaResourceBase
from oktapy.resources.user import User


class UserMgr(OktaResourceBase):
    """User manager class.

    Inherits from OktaResourceBase class.
    User manager is responsible for executing Okta user operations.
    More details on Okta user APIs - https://developer.okta.com/docs/reference/api/users/


    Attributes
    ----------
    _url : object
        Relative URL of Okta user API endpoint - /api/v1/users

    Methods
    -------
    activateUser(id)
        Activates a staged user.

    createUsers(input)
        Creates a user

    deactivateUser(id)
        Deactivates an active or suspended user

    deleteUser(id)
        Deletes a deactivated user

    getCurrentUser()
        Returns the current user

    getUser(idOrLogin)
        Get the user with supplied `ID` or `login`

    getUsers()
        Returns all users

    reactivateUser(id)
        Reactivates a deactivated user

    searchUser(query)
        Searches users based on query
    """

    def __init__(self, client):
        """

        Instantiates an user manager object.

        Parameters
        ----------
        client : object
            Okta client object to associate. Can be an instance of OktaAPIToken or OktaOAuth class.
            Sets the relative URL of Okta user API endpoint to `/api/v1/users`
        """

        super(UserMgr, self).__init__(client)
        self._url = '/api/v1/users'

    def activateUser(self, id):
        pass

    def createUsers(self, input):
        apiurl = self._url
        result = self._client.request(apiurl, self, mode='post', data=input)
        return result

    def deactivateUser(self, id):
        pass

    def deleteUser(self, id):
        apiurl = self._url + "/" + id
        return self._client.request(apiurl, self, mode="delete")

    def getCurrentUser(self):
        """Returns the current user.

         If the mode is `apitoken`, this method returns the owner of the API token.
         Otherwise if the mode is `oauth`, it returns the user, the token is issued for.
         The returned object is an instance of the `User` class.
        """

        apiurl = self._url + '/me'
        return User(self._client.request(apiurl, self))

    def getUser(self, idOrLogin):
        """Get the user with supplied `ID` or `login`.

        Parameters
        ----------
        idOrLogin : str
            Either the internal Okta user ID or login attribute value
        """
        apiurl = self._url + "/" + idOrLogin
        return User(self._client.request(apiurl, self))

    def getUsers(self):
        apiurl = self._url
        return list(map(User, self._client.request(apiurl, self)))

    def reactivateUser(self, id):
        pass

    def searchUser(self, query):
        pass
