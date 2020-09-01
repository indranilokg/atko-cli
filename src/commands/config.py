import click
import json
import configparser
from json.decoder import JSONDecodeError


@click.group(invoke_without_command=True)
@click.option("--profile", "-p")
@click.pass_context
def cli(ctx, profile):
    """Store configuration values."""

    if ctx.invoked_subcommand is None:
        if profile is None:
            profile = "DEFAULT"

        config_file = ctx.obj.get("config_file")
        creds_file = ctx.obj.get("creds_file")

        _createProfile(profile, config_file, creds_file)


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help='Profile details')
@click.pass_context
def list(ctx, verbose):
    """List profile names."""

    config = ctx.obj.get("config")
    creds = ctx.obj.get("creds")

    for profile in config:
        if(verbose):
            click.echo(f"Profile: {profile}")
            click.echo("_________________________")
            for key in config[profile]:
                click.echo(f"{key}: {config[profile][key]}")
            for key in creds[profile]:
                click.echo(f"{key}: {creds[profile][key]}")
            click.echo("_________________________")
            click.echo("                         ")
            click.echo("                         ")
        else:
            click.echo(f"{profile}")


@cli.command()
@click.option("--profile", "-p", prompt="Enter profile name")
@click.pass_context
def show(ctx, profile):
    """Show current profile."""

    config = ctx.obj.get("config")
    creds = ctx.obj.get("creds")
    try:
        for key in config[profile]:
            click.echo(f"{key}: {config[profile][key]}")
        for key in creds[profile]:
            click.echo(f"{key}: {creds[profile][key]}")
    except KeyError as err:
        raise click.ClickException("Enter a valid profile name. Run `okt config list` to find the confgured profiles.") from err


@cli.command()
@click.option("--clear", "-c", is_flag=True, help="Clear cache")
@click.option("--remove", "-r", help="Remove cache entry")
@click.option("--key", "-k", help="Cached profile name")
@click.pass_context
def cache(ctx, clear, remove, key):
    """Access OAuth cache."""

    cachefile = ctx.obj.get("cache_file")
    try:
        with open(cachefile, 'r') as infile:
            oauthCache = json.load(infile)
        if clear:
            if click.confirm("Clear the OAuth cache?"):
                with open(cachefile, 'w') as outfile:
                    oauthCache = json.dump({}, outfile)
                click.echo("Cache cleared")
        elif remove is not None:
            if click.confirm("Remove the cache entry?"):
                _removeCacheEntry(oauthCache, remove)
                with open(cachefile, 'w') as outfile:
                    json.dump(oauthCache, outfile)
        elif key is not None:
            entry = _getCacheEntry(oauthCache, key)
            click.echo(json.dumps(entry, indent=4))
        else:
            for cache in oauthCache:
                click.echo(cache)
    except JSONDecodeError as err:
        raise click.ClickException("Could not access the cache file.") from err


def _getCacheEntry(oauthCache, key):
    entry = {}
    lst = key.split(":")
    profile = lst[0]
    resource = None
    if (len(lst) == 1):
        entry = oauthCache.get(profile, {})
    elif (len(lst) == 2):
        resource = lst[1]
        entry = oauthCache.get(profile, {}).get(resource, {})
    elif (len(lst) == 3):
        resource = lst[1]
        token_type = lst[2]
        entry = oauthCache.get(profile, {}).get(resource, {}).get(token_type, {})
    else:
        raise click.ClickException("Invalid key.")
    return entry


def _removeCacheEntry(oauthCache, key):
    entry = {}
    lst = key.split(":")
    profile = lst[0]
    resource = None
    if (len(lst) == 1):
        oauthCache.pop(profile, {})
    elif (len(lst) == 2):
        resource = lst[1]
        entry = oauthCache.get(profile, {}).pop(resource, {})
    elif (len(lst) == 3):
        resource = lst[1]
        token_type = lst[2]
        entry = oauthCache.get(profile, {}).get(resource, {}).pop(token_type, {})
    else:
        raise click.ClickException("Invalid key.")
    return entry


def _createProfile(profile, config_file, creds_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    creds = configparser.ConfigParser()
    creds.read(creds_file)

    base_url = click.prompt(
        "Enter Okta Org URL",
        default="https://example.okta.com"
    )

    api_mode = click.prompt(
        "Enter API mode (token/oauth)",
        default="token"
    )

    if api_mode == "token":
        config[profile] = {
            "base_url": base_url,
            "api_mode": api_mode,
            "grant_type": ""
        }

        creds[profile] = _getTokenCreds()

    elif api_mode == "oauth":
        grant_type = click.prompt(
            "Enter OAuth Grant Type",
            default="password"
        )

        config[profile] = {
            "base_url": base_url,
            "api_mode": api_mode,
            "grant_type": grant_type
        }

        creds[profile] = _getOAuthCreds(grant_type)
    else:
        raise click.ClickException(f"Invalid mode {api_mode}")

    with open(config_file, "w") as cfgfile:
        config.write(cfgfile)

    with open(creds_file, "w") as credsfile:
        creds.write(credsfile)


def _getTokenCreds():
    api_token = click.prompt(
        "Enter API Token",
        default=""
    )

    credsObject = {
        "api_token": api_token,
        "client_id": "",
        "client_secret": "",
        "redirect_uri": "",
        "jwk": "",
        "user_id": "",
        "user_password": ""
    }

    return credsObject


def _getOAuthCreds(grant_type):
    credsObject = {}
    if grant_type == "password":
        client_id = click.prompt(
            "Enter OAuth Client ID",
            default=""
        )

        client_secret = click.prompt(
            "Enter Client Secret",
            default="password"
        )

        user_id = click.prompt("Enter Okta User ID")

        user_password = click.prompt("Enter Password", hide_input=True)

        credsObject = {
            "client_id": client_id,
            "client_secret": client_secret,
            "api_token": "",
            "redirect_uri": "",
            "jwk": "",
            "user_id": user_id,
            "user_password": user_password
        }
    elif grant_type == "implicit":
        client_id = click.prompt(
            "Enter OAuth Client ID",
            default=""
        )

        redirect_uri = click.prompt(
            "Enter Redirect URI",
            default="http://127.0.0.1:12345"
        )

        credsObject = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "api_token": "",
            "client_secret": "",
            "jwk": "",
            "user_id": "",
            "user_password": ""
        }
    elif grant_type == "authorization_code":
        client_id = click.prompt(
            "Enter OAuth Client ID",
            default=""
        )

        client_secret = click.prompt(
            "Enter Client Secret",
            default=""
        )

        redirect_uri = click.prompt(
            "Enter Redirect URI",
            default="http://127.0.0.1:12345"
        )

        credsObject = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "api_token": "",
            "jwk": "",
            "user_id": "",
            "user_password": ""
        }
    elif grant_type == "pkce":
        client_id = click.prompt(
            "Enter OAuth Client ID",
            default=""
        )

        redirect_uri = click.prompt(
            "Enter Redirect URI",
            default="http://127.0.0.1:12345"
        )

        credsObject = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "api_token": "",
            "client_secret": "",
            "jwk": "",
            "user_id": "",
            "user_password": ""
        }
    elif grant_type == "client_credentials":
        client_id = click.prompt(
            "Enter OAuth Client ID",
            default=""
        )

        jwkFile = click.prompt(
            "Enter JWK file"
        )

        with open(jwkFile, 'r') as f:
            jwk = json.load(f)

        credsObject = {
            "client_id": client_id,
            "jwk": jwk,
            "api_token": "",
            "client_secret": "",
            "redirect_uri": "",
            "user_id": "",
            "user_password": ""
        }
    else:
        raise click.ClickException(f"Invalid oauth grant type {grant_type}")
    return credsObject
