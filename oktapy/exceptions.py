
"""This module has the exception classes for the library defined.

The library can throw different classes of exceptions. Those classes are:

    * APIException - Exception class for errors related to REST calls
    * ServiceException - Exception class for errors related to Okta API calls
    * ConfigurationException - Exception class for configuration errors
"""


class APIException(Exception):
    def __init__(self, message, source_exception=None):
        """Exception class for errors related to REST calls.

        Wraps the original exception thrown during an REST call.

        Parameters
        ----------
        message : str
            Summary error message
        source_exception : Exception
            Original exception thrown during REST operation.
        """

        super(APIException, self).__init__({
            "message": message,
            "error": source_exception
        })
        self.source = source_exception


class ServiceException(Exception):
    def __init__(self, status=None, code=None, message=None, info=None):
        """Exception class for errors related to Okta API calls.

        Captures the errors returned from Okta during an API operation.

        Parameters
        ----------
        status : str
            Okta API operation status
        code : str
            Error code returned by Okta
        message : str
            Summary error message
        info : object
            Detail information about the API operation. For example - response object returned by Okta
        """

        self.status = status
        self.code = code
        self.message = message
        self.info = info

        if not message:
            message = "Okta Service Exception"

        super(ServiceException, self).__init__({
            "code": code,
            "message": message,
            "status": status,
            "info": info
        })


class ConfigurationException(Exception):
    """Exception class for configuration errors.

    Captures the library configuration errors. These errors are raised when the library methods
    are called with invalid or unsupported arguments.

    Parameters
    ----------
    message : str
        Error message
    """

    def __init__(self, message):
        super(ConfigurationException, self).__init__('ConfigurationException: ' + message)
        self.message = message


"""
class AuthException(Exception):
    def __init__(self, code = None, message = None, info = None):
        self.code = code
        self.message = message
        self.info = info

        if not message:
            message = "Auth Exception"

        super(AuthException, self).__init__({
            "code": code,
            "message": message,
            "info": info
        })

class TokenException(Exception):
    def __init__(self, code = None, message = None, info = None):
        self.code = code
        self.message = message
        self.info = info

        if not message:
            message = "Token Exception"

        super(TokenException, self).__init__({
            "code": code,
            "message": message,
            "info": info
        })

class ClientException(Exception):
    def __init__(self, message):
        super(ClientException, self).__init__('ClientException: ' + message)
        self.message = message
"""
