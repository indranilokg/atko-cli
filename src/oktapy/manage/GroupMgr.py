from oktapy.resources.group import Group
import pandas as pd
import json

class GroupMgr:
    def __init__(self, client):
        self._client = client
        self._base_url = "/api/v1/groups"

    @staticmethod
    def to_frame(group_list):
        data = pd.DataFrame([group.to_dict() for group in group_list])
        data.fillna('', inplace=True)
        data.sort_index(axis=1, inplace=True)
        return data

    def list(self, query=None, filter=None, limit=20):
        apiurl = self._base_url
        if query or filter or limit:
            apiurl += "?"
            if query:
                apiurl += f"q={query}&"
            if filter:
                apiurl += f"filter={filter}&"
            if limit:
                apiurl += f"limit={limit}&"
            apiurl = apiurl.rstrip("&")
        result, _ = self._client.request(apiurl, self)
        return [Group(data) for data in result]

    def create(self, data):
        """Create a new group"""
        # Ensure data is properly formatted as JSON
        if isinstance(data, dict):
            data = json.dumps(data)
        response = self._client.request(self._base_url, self, mode="post", data=data)
        # Handle both tuple response and direct response cases
        if isinstance(response, tuple):
            result, _ = response
            return result
        return response

    def get(self, group_id):
        result, _ = self._client.request(f"{self._base_url}/{group_id}", self)
        return result

    def delete(self, group_id):
        """Delete a group"""
        response = self._client.request(f"{self._base_url}/{group_id}", self, mode="delete")
        # DELETE returns 204 No Content on success
        if isinstance(response, int) and response == 204:
            return True
        result, _ = response
        return result

    def list_users(self, group_id, limit=200):
        """List users in a group"""
        url = f"{self._base_url}/{group_id}/users"
        if limit:
            url += f"?limit={limit}"
        result, next_url = self._client.request(url, self)
        return result

    def add_user(self, group_id, user_id):
        """Add a user to a group"""
        url = f"{self._base_url}/{group_id}/users/{user_id}"
        response = self._client.request(url, self, mode="put")
        if response is None or (isinstance(response, int) and response == 204):
            return True
        if isinstance(response, tuple):
            result, _ = response
            return result
        return response

    def remove_user(self, group_id, user_id):
        """Remove a user from a group"""
        response = self._client.request(f"{self._base_url}/{group_id}/users/{user_id}", self, mode="delete")
        # DELETE returns 204 No Content on success
        if isinstance(response, int) and response == 204:
            return True
        result, _ = response
        return result

    def list_apps(self, group_id, limit=20):
        apiurl = f"{self._base_url}/{group_id}/apps?limit={limit}"
        result, _ = self._client.request(apiurl, self)
        return result 