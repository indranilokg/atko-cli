from oktapy.manage.OktaResourceBase import OktaResourceBase
from oktapy.resources.user import User
from oktapy.exceptions import ServiceException
import pandas as pd
import json


def to_frame(user_list):
    data = pd.DataFrame([user.to_dict() for user in user_list])
    data.fillna('', inplace=True)
    data.sort_index(axis=1, inplace=True)
    return data


def to_users_json_from_csv(file, options={}):
    list_of_users = []
    df = pd.read_csv(file, index_col=False)
    df = df.drop(["id", "status"], axis=1, errors='ignore')
    fallThrough = True
    selectors = list({"default-password", "no-password", "import-password",
                      "hashed-password"}.intersection((list(options.keys()))))
    if selectors:
        if "default-password" in selectors:
            df = df.drop(["password"], axis=1, errors='ignore')
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(map(lambda x: {"profile": x, "credentials": {
                "password": {"value": options["default-password"]}}}, records))
            fallThrough = False
        elif "no-password" in selectors:
            df = df.drop(["password"], axis=1, errors='ignore')
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(
                map(lambda x: {"profile": x}, records))
            fallThrough = False
        elif "import-password" in selectors:
            df = df.drop(["password"], axis=1, errors='ignore')
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(map(lambda x: {"profile": x, "credentials": {
                "password": {"hook": {"type": "default"}}}}, records))
            fallThrough = False
        elif ("hashed-password" in selectors) and ("password" in df.columns):
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(map(lambda x: {"profile": x,
                                                "credentials": {
                                                    "password": {
                                                        "hash": {
                                                            "algorithm": "BCRYPT",
                                                            "workFactor": 10,
                                                            "salt": "rwh3vH166HCH/NT9XV5FYu",
                                                            "value": x.pop("password")
                                                        }
                                                    }
                                                }
                                                },
                                     records))

            fallThrough = False
        else:
            fallThrough = True
    if fallThrough:
        if "password" in df.columns:
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(map(lambda x: {"profile": x, "credentials": {
                "password": {"value": x.pop("password")}}}, records))
        else:
            records = json.loads(df.to_json(orient="records"))
            list_of_users = list(
                map(lambda x: {"profile": x}, records))
    return list_of_users


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

    def createUser(self, payload, activate=False):
        apiurl = self._url + "?activate=" + str(activate).lower()
        return self._client.request(apiurl, self, mode="post", data=payload)

    def createUsers(self, inputs=[], file=None, mode="json", options={}, source="input", activate=False):
        result = {},
        success = []
        failure = []
        errors = []

        list_of_users = []
        list_of_users2 = []

        if file is None:
            list_of_users = inputs
        else:
            if mode == "csv":
                list_of_users2 = to_users_json_from_csv(file, options)
                print(list_of_users2)
            else:
                with open(file, 'r') as infile:
                    data = json.load(infile)
                    if isinstance(data, list):
                        list_of_users = data
                    else:
                        list_of_users = [data]

        for userdata in list_of_users:
            try:
                payload = json.dumps(userdata)
                response = self.createUser(payload, activate=activate)
            except ServiceException as ex:
                errors.append(ex.info)
                failure.append(userdata)
            except Exception as ex:
                errors.append(ex.message)
                failure.append(userdata)
            else:
                success.append(response["profile"]["login"])

        result = {"success": success, "failure": failure, "errors": errors}
        return result

    def deactivateUser(self, id, notify=False):
        apiurl = self._url + "/" + id + \
            "/lifecycle/deactivate?sendEmail=" + str(notify).lower()
        return self._client.request(apiurl, self, mode="post")

    def deactivateUsers(self, ids, notify=False):
        result = {},
        success = []
        failure = []
        errors = []

        for rid in ids:
            try:
                self.deactivateUser(rid, notify=notify)
            except ServiceException as ex:
                errors.append(ex.info)
                failure.append(rid)
            except Exception as ex:
                errors.append(ex.message)
                failure.append(rid)
            else:
                success.append(rid)

        result = {"success": success, "failure": failure, "errors": errors}
        return result

    def deleteUser(self, id, notify=False):
        apiurl = self._url + "/" + id + "?sendEmail=" + str(notify).lower()
        return self._client.request(apiurl, self, mode="delete")

    def deleteUsers(self, ids, notify=False):
        result = {},
        success = []
        failure = []
        errors = []

        for rid in ids:
            try:
                self.deleteUser(rid, notify=notify)
            except ServiceException as ex:
                errors.append(ex.info)
                failure.append(rid)
            except Exception as ex:
                errors.append(ex.message)
                failure.append(rid)
            else:
                success.append(rid)

        result = {"success": success, "failure": failure, "errors": errors}
        return result

    def getCurrentUser(self, attr=None):
        """Returns the current user.

         If the mode is `apitoken`, this method returns the owner of the API token.
         Otherwise if the mode is `oauth`, it returns the user, the token is issued for.
         The returned object is an instance of the `User` class.
        """

        apiurl = self._url + '/me'
        result, link = self._client.request(apiurl, self)
        user = User(result, links=False, attr=attr)
        return user

    def getUser(self, idOrLogin, attr=None):
        """Get the user with supplied `ID` or `login`.

        Parameters
        ----------
        idOrLogin : str
            Either the internal Okta user ID or login attribute value
        """
        apiurl = self._url + "/" + idOrLogin
        result, link = self._client.request(apiurl, self)
        user = User(result, attr=attr)
        return user

    def getUsers(self, query=None, filter=None, search=None, attr=None, limit=200, threshold=0, deepSearch={}):
        apiurl = self._url
        result_arr = []

        if (query is not None) and (len(query.strip()) > 0):
            if threshold > 0:
                apiurl = apiurl + "?limit=" + str(threshold) + "&q=" + query
            else:
                apiurl = apiurl + "?q=" + query
            result, next = self._client.request(apiurl, self)
            result_arr = result
        else:
            if (filter is not None) and (len(filter.strip()) > 0):
                apiurl = apiurl + "?limit=" + str(limit) + "&filter=" + filter
            elif (search is not None) and (len(search.strip()) > 0):
                apiurl = apiurl + "?limit=" + str(limit) + "&search=" + search
            else:
                apiurl = apiurl + "?limit=" + str(limit)

            result, next = self._client.request(apiurl, self)

            if (threshold > 0) and (threshold <= limit):
                result_arr = result[:threshold]
            else:
                result_arr = result
                while next:
                    result, next = self._client.request(next, self)
                    delta = threshold - len(result_arr)
                    if (threshold > 0) and (delta <= limit):
                        result_arr = result_arr + result[:delta]
                        break
                    else:
                        result_arr = result_arr + result
        user_list = list(map(lambda d: User(d, attr=attr), result_arr))
        if deepSearch:
            user_list = self.deep_search(user_list, deepSearch)
        return user_list

    def deep_search(self, user_list, deepSearch):
        print("Deep Search")
        df = to_frame(user_list)
        cols = list(set(list(deepSearch.keys())
                        ).intersection(list(df.columns)))
        if len(cols) == 0:
            return user_list
        else:
            d_search = {key: deepSearch[key] for key in cols}
            id_list = df["id"].tolist()
            for k in d_search:
                col_id_list = df[df[k].str.contains(
                    deepSearch[k])]["id"].tolist()
                id_list = list(set(col_id_list).intersection(id_list))
            new_list = [user for user in user_list if user["id"] in id_list]
            return new_list

    def reactivateUser(self, id):
        pass
