CONFIG_KEY_OAUTH_FLOW = "OAUTH_FLOW"
OAuthConfigAllowedFlows = ['manual', 'password',
                           'client_credentials', 'pkce', 'authorization_code', 'implicit']
CONFIG_KEY_CLIENT_ID = "client_id"
CONFIG_KEY_CLIENT_SECRET = "client_secret"
CONFIG_KEY_AUTH_SERVER = "auth_server"
CONFIG_KEY_REDIRECT_URI = "redirect_uri"
CONFIG_KEY_USER_ID = "userid"
CONFIG_KEY_USER_PWD = "password"
CONFIG_KEY_CLIENT_ASSERTION = "client_assertion"
CONFIG_KEY_JWK = "jwk"


O4O_SCOPE_MAP = {
    "UserMgr":
    [
        "okta.users.manage",
        "okta.users.read",
        "okta.users.manage.self",
        "okta.users.read.self"
    ]
}

O4O_SERVICE_SCOPE_MAP = {
    "UserMgr":
    [
        "okta.users.manage",
        "okta.users.read"
    ]
}
