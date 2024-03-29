import click
import json
import os
import functools
import webbrowser
import socket
import time
from json.decoder import JSONDecodeError
from oktapy.okta import Okta
from urllib import parse
from wsgiref import simple_server
from click import Option, UsageError

_global_options = [
    click.option('--profile', '-p', default="DEFAULT", envvar='ATKO_PROFILE', help='Profile name'),
    click.option('--debug', is_flag=True, help="Debug information on Exceptions"),
    click.option('--output', '-o', default="stdout", help='Output format')
]

# //TODO: Rename file to core.py

class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This option is mutually exclusive with '
                ' options: [' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "options `{}`.".format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


class DependentOption(Option):
    def __init__(self, *args, **kwargs):
        self.dependent_on = set(kwargs.pop('dependent_on', []))
        help = kwargs.get('help', '')
        if self.dependent_on:
            ex_str = ', '.join(self.dependent_on)
            kwargs['help'] = help + (
                ' NOTE: This option is dependent on '
                ' options: [' + ex_str + '].'
            )
        super(DependentOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if (self.name in opts) and (not self.dependent_on.intersection(opts)):
            raise UsageError(
                "Illegal usage: `{}` is dependent on "
                "options `{}`.".format(
                    self.name,
                    ', '.join(self.dependent_on)
                )
            )

        return super(DependentOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print("Finished {} in {} secs".format(repr(func.__name__), round(run_time, 3)))
        return value

    return wrapper


def _get_server(app):
    port = 12345
    try:
        server = simple_server.make_server('0.0.0.0', port, app)
        return server
    except socket.error:
        raise click.ClickException(f"Port {port} is not available")


def global_options(func):
    for option in reversed(_global_options):
        func = option(func)
    return func


def get_profile(ctx, profilename):
    _profile_details = {}
    _config = ctx.obj.get("config")
    _credentials = ctx.obj.get("credentials")
    for key in _config[profilename]:
        _profile_details[key] = _config[profilename][key]
    for key in _credentials[profilename]:
        _profile_details[key] = _credentials[profilename][key]
    return _profile_details


def get_okta_provider(ctx, profilename):
    _profile = get_profile(ctx, profilename)
    _mode = _profile["api_mode"]
    if _mode == "token":
        _provider = Okta(_profile["base_url"],
                         token=_profile["api_token"])
    elif _mode == "oauth":
        _provider = Okta(_profile["base_url"],
                         mode="oauth",
                         oauthConfig=_get_oauth_config(_profile))
    else:
        raise click.ClickException(f"Invalid mode {_mode}")
    return _provider


def _get_oauth_config(profile):
    _config = {}
    _grant_type = profile["grant_type"]
    if _grant_type == "password":
        _config = {
            "OAUTH_FLOW": _grant_type,
            "client_id": profile["client_id"],
            "client_secret": profile["client_secret"],
            "userid": profile["user_id"],
            "password": profile["user_password"]}
    elif _grant_type == "implicit":
        _config = {
            "OAUTH_FLOW": _grant_type,
            "client_id": profile["client_id"],
            "redirect_uri": profile["redirect_uri"]}
    elif _grant_type == "authorization_code":
        _config = {
            "OAUTH_FLOW": _grant_type,
            "client_id": profile["client_id"],
            "client_secret": profile["client_secret"],
            "redirect_uri": profile["redirect_uri"]}
    elif _grant_type == "pkce":
        _config = {
            "OAUTH_FLOW": _grant_type,
            "client_id": profile["client_id"],
            "redirect_uri": profile["redirect_uri"]}
    elif _grant_type == "client_credentials":
        _config = {
            "OAUTH_FLOW": _grant_type,
            "client_id": profile["client_id"],
            "jwk": json.loads(profile["jwk"].replace("\'", "\""))}
    return _config


def _get_cached_token(cache, profilename, resource):
    try:
        with open(cache, 'r') as infile:
            _oauth_cache = json.load(infile)
    except JSONDecodeError:
        _oauth_cache = {}

    access_token, refresh_token = None, None

    tokencache = _oauth_cache.get(profilename)
    if tokencache is not None:
        profile_resource = tokencache.get(resource)
        if profile_resource is not None:
            access_token, refresh_token = profile_resource.get("access_token", None), profile_resource.get("refresh_token", None)
    return access_token, refresh_token


def _set_cached_token(cache, profilename, resource, token, refresh_token):
    try:
        with open(cache, 'r') as infile:
            _oauth_cache = json.load(infile)
    except JSONDecodeError:
        if os.stat(cache).st_size == 0:
            _oauth_cache = {}
        else:
            raise click.ClickException('Corrupt cache file. Remove the cache and retry.')

    # _oauth_cache[profilename] = {"access_token": token, "refresh_token": refresh_token}

    profile = _oauth_cache.get(profilename, {})
    profile[resource] = {"access_token": token, "refresh_token": refresh_token}
    _oauth_cache[profilename] = profile

    with open(cache, 'w') as outfile:
        _oauth_cache = json.dump(_oauth_cache, outfile)


def _authenticate_handler(profilename, profile, handler, resource, cache):
    code_or_token = ""

    def callback(environ, start_response):
        nonlocal code_or_token
        nonlocal grant_type
        if grant_type == "implicit":
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0
            request_body = environ['wsgi.input'].read(request_body_size).decode("utf-8")
            params = parse.parse_qs(request_body, encoding="utf-8")
            code_or_token = params["access_token"][0]
        else:
            query = environ['QUERY_STRING']
            split = query.split('&')
            kv = dict([v.split('=', 1) for v in split])

            if 'error' in kv:
                code_or_token = False
                raise Exception(f"Error code returned: {kv['error']} ({kv.get('error_description')})")
            else:
                code_or_token = kv['code']

        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [u'Logged in. You can close this window and return to the CLI'.encode('ascii')]

    generate_new_token = True
    grant_type = profile['grant_type']
    token, refresh_token = _get_cached_token(cache, profilename, resource)
    if token is not None:
        if handler.isTokenValid(token):
            print("Valid token")
            generate_new_token = False
            handler.setToken(token=token, verify=False)
            handler.setTokenVerified(True)
        else:
            if grant_type in ['authorization_code', 'password']:
                print("Attempting to renew token from Refresh Token")
                try:
                    token, refresh_token = handler.generateNewToken(refresh_token=refresh_token)
                except Exception:
                    generate_new_token = True
                else:
                    generate_new_token = False
                    handler.setToken(token=token, verify=False)
                    handler.setTokenVerified(True)
                    _set_cached_token(cache, profilename, resource, token, refresh_token)
            else:
                generate_new_token = True

    else:
        if (grant_type in ['authorization_code', 'password']) and (refresh_token is not None):
            print("Attempting to renew token from Refresh Token")
            try:
                token, refresh_token = handler.generateNewToken(refresh_token=refresh_token)
            except Exception:
                generate_new_token = True
            else:
                generate_new_token = False
                handler.setToken(token=token, verify=False)
                handler.setTokenVerified(True)
                _set_cached_token(cache, profilename, resource, token, refresh_token)
        else:
            generate_new_token = True

    if(generate_new_token):
        print("Get a new token")
        if grant_type in ['pkce', 'authorization_code', 'implicit']:
            url = handler.initAuth()
            print(url)
            webbrowser.open(url)
            server = _get_server(callback)
            if not server:
                raise click.ClickException('We were unable to instantiate a webserver')
            server.handle_request()
            server.server_close()
            token, refresh_token = handler.authenticate(input=code_or_token, verify=False)
        elif grant_type in ['password', 'client_credentials']:
            token, refresh_token = handler.authenticate(verify=False, passive=True)
        handler.setTokenVerified(True)
        _set_cached_token(cache, profilename, resource, token, refresh_token)


def get_handler(ctx, profilename, resource):
    profile = get_profile(ctx, profilename)
    mode = profile['api_mode']
    provider = get_okta_provider(ctx, profilename)
    if resource == "user":
        handler = provider.UserMgr()
    if mode == "oauth":
        _authenticate_handler(profilename, profile, handler, resource, ctx.obj.get("cache_file"))
    return handler
