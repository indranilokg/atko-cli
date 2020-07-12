import requests

from oktapy.exceptions import APIException, ServiceException


class OktaRequest(object):
    """Okta API request handler class.

    This class handles the actual HTTPS API call to Okta endpoints.

    Attributes
    ----------
    _headers : Object
        HTTP header key-value pairs

    Methods
    -------
    get(url, headers=None)
        Executes HTTP GET call to the supplied Okta endpoint and returns the reesponse.

    post(url, data=None, headers=None)
        Executes HTTP POST call to the supplied Okta endpoint and returns the reesponse.

    delete(url, headers=None)
        Executes HTTP DELETE call to the supplied Okta endpoint and returns the reesponse.
    """

    def __init__(self):
        """

        Instantiates OktaRequest handler object and bootstraps the default HTTP header key-value pairs.
        Since most of the API's deal with JSON data, `Content-Type` and `Accept` headers are set to
        `application/json`
        """

        self._headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    def _httpcall(self, url, data=None, headers=None, mode="get"):
        """Internal common function to execute REST API call.

        Parameters
        ----------
        url : str
            Okta API endpoint. Example - https://example.okta.com/api/v1/users
        data : object, optional
            Payload data for the API endpoint (default is None).
        headers : object, optional
            HTTP header key-value pairs specific to the API endpoint (default is None).
        mode : str
            HTTP Call type. Allowed value - `get`, `post`, `delete`, `put`, `patch` (default is `get`).

        Raises
        ------
        APIException
            Exception related to  HTTP REST calls.
        ServiceException
            Exception related to Okta API calls.
        """

        final_headers = self._headers.copy()
        final_headers.update(headers or {})

        try:
            res = requests.models.Response()
            if mode == "get":
                res = requests.get(url, headers=final_headers)
                result = res.json()
            elif mode == "post":
                print(data)
                print(final_headers)
                res = requests.post(url, data=data, headers=final_headers)
                result = res.json()
            elif mode == "delete":
                print(final_headers)
                res = requests.delete(url, headers=final_headers)
                result = res.status_code
            else:
                raise APIException(f"HTTP {mode} is not supported", None)

            res.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                result = res.json()
                if result.get("errorCode") is not None:
                    raise ServiceException(
                        status=res.status_code,
                        code=result["errorCode"],
                        message="Okta Service Exception",
                        info=result
                    )
                elif result.get("error") is not None:
                    raise ServiceException(
                        status=res.status_code,
                        code=result["error"],
                        message="Okta Service Exception",
                        info=result
                    )
                else:
                    raise ServiceException(
                        status=res.status_code,
                        code="unknown_error",
                        message="Okta Service Exception",
                        info=result
                    )
            except Exception:
                raise ServiceException(
                    status=res.status_code,
                    code="api_error",
                    message="Okta Service Exception",
                    info=res
                )
        except requests.exceptions.ConnectionError as errc:
            raise APIException("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            raise APIException("Timeout Error:", errt)
        except requests.exceptions.TooManyRedirects as errr:
            raise APIException("Too Many Redirects Error:", errr)
        except requests.exceptions.RequestException as err:
            raise APIException("OOps: Something Else", err)
        except ValueError:
            raise APIException("Failed to parse API response", res)

        return result

    def get(self, url, headers=None):
        """Executes HTTP GET call to the supplied Okta endpoint and returns the response.

        Parameters
        ----------
        url : str
            Okta API endpoint. Example - https://example.okta.com/api/v1/users
        headers : object, optional
            HTTP header key-value pairs specific to the API endpoint (default is None).
        """

        return self._httpcall(url=url, headers=headers, mode="get")

    def post(self, url, data=None, headers=None):
        """Executes HTTP GET call to the supplied Okta endpoint and returns the response.

        Parameters
        ----------
        url : str
            Okta API endpoint. Example - https://example.okta.com/api/v1/users
        data : object, optional
            Payload data for the API endpoint (default is None).
        headers : object, optional
            HTTP header key-value pairs specific to the API endpoint (default is None).
        """

        return self._httpcall(url=url, headers=headers, data=data, mode="post")

    def delete(self, url, headers=None):
        """Executes HTTP DELETE call to the supplied Okta endpoint and returns the response.

        Parameters
        ----------
        url : str
            Okta API endpoint. Example - https://example.okta.com/api/v1/users/${userId}
        headers : object, optional
            HTTP header key-value pairs specific to the API endpoint (default is None).
        """

        return self._httpcall(url=url, headers=headers, mode="delete")
