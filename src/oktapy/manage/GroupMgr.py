from oktapy.manage.OktaResourceBase import OktaResourceBase
from oktapy.resources.group import Group
from oktapy.exceptions import ServiceException
import pandas as pd
import json


def to_frame(group_list):
    data = pd.DataFrame([group.to_dict() for group in group_list])
    data.fillna('', inplace=True)
    data.sort_index(axis=1, inplace=True)
    return data


def to_groups_json_from_csv(file, options={}):
    list_of_groups = []
    df = pd.read_csv(file, index_col=False)
    newdf = pd.DataFrame(columns=["name", "description"])
    # df = df[["name", "description"]]
    newdf["name"] = df.get("name")
    newdf["description"] = df.get("description")
    newdf.fillna("", inplace=True)
    records = json.loads(newdf.to_json(orient="records"))
    list_of_groups = list(
        map(lambda x: {"profile": x}, records))
    return list_of_groups


class GroupMgr(OktaResourceBase):
    """Group manager class.

    Inherits from OktaResourceBase class.
    Group manager is responsible for executing Okta group operations.
    More details on Okta groups APIs - https://developer.okta.com/docs/reference/api/groups/


    Attributes
    ----------
    _url : object
        Relative URL of Okta groups API endpoint - /api/v1/groups

    Methods
    -------
    """

    def __init__(self, client):
        """

        Instantiates a group manager object.

        Parameters
        ----------
        client : object
            Okta client object to associate. Can be an instance of OktaAPIToken or OktaOAuth class.
            Sets the relative URL of Okta group API endpoint to `/api/v1/groups`
        """

        super(GroupMgr, self).__init__(client)
        self._url = '/api/v1/groups'

    def createGroup(self, payload):
        apiurl = self._url
        return self._client.request(apiurl, self, mode="post", data=payload)

    def createGroups(self, inputs=[], file=None, mode="json", options={}, source="input", activate=False):
        result = {},
        success = []
        failure = []
        errors = []

        list_of_groups = []

        if file is None:
            list_of_groups = inputs
        else:
            if mode == "csv":
                list_of_groups = to_groups_json_from_csv(file, options)
            else:
                with open(file, 'r') as infile:
                    data = json.load(infile)
                    if isinstance(data, list):
                        list_of_groups = data
                    else:
                        list_of_groups = [data]
        print(list_of_groups)
        for groupdata in list_of_groups:
            try:
                payload = json.dumps(groupdata)
                response = self.createGroup(payload)
            except ServiceException as ex:
                errors.append(ex.info)
                failure.append(groupdata)
            except Exception as ex:
                errors.append(ex.message)
                failure.append(groupdata)
            else:
                success.append(response["profile"]["name"])

        result = {"success": success, "failure": failure, "errors": errors}
        return result

    def deleteGroup(self, id):
        apiurl = self._url + "/" + id
        return self._client.request(apiurl, self, mode="delete")

    def deleteGroups(self, ids):
        result = {},
        success = []
        failure = []
        errors = []

        for rid in ids:
            try:
                self.deleteGroup(rid)
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

    def getGroup(self, id):
        """Get the group with supplied `ID`

        Parameters
        ----------
        id : str
            Internal Okta group ID
        """
        apiurl = self._url + "/" + id
        result, link = self._client.request(apiurl, self)
        group = Group(result)
        return group

    def getGroups(self, query=None, filter=None, search=None, limit=200, threshold=0, deepSearch={}):
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
        group_list = list(map(lambda d: Group(d), result_arr))
        if deepSearch:
            group_list = self.deep_search(group_list, deepSearch)
        return group_list

    def deep_search(self, group_list, deepSearch):
        print("Deep Search")
        df = to_frame(group_list)
        cols = list(set(list(deepSearch.keys())
                        ).intersection(list(df.columns)))
        if len(cols) == 0:
            return group_list
        else:
            d_search = {key: deepSearch[key] for key in cols}
            id_list = df["id"].tolist()
            for k in d_search:
                col_id_list = df[df[k].str.contains(
                    deepSearch[k])]["id"].tolist()
                id_list = list(set(col_id_list).intersection(id_list))
            new_list = [group for group in group_list if group["id"] in id_list]
            return new_list
