import click
import configparser
import json

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
        credential_file = ctx.obj.get("credential_file")

        _create_profile(profile, config_file, credential_file)


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help='Profile details')
@click.pass_context
def list(ctx, verbose):
    """List profile names."""

    config = ctx.obj.get("config")
    credentials = ctx.obj.get("credentials")

    for profile in config:
        if(verbose):
            click.echo(f"Profile: {profile}")
            click.echo("_________________________")
            for key in config[profile]:
                click.echo(f"{key}: {config[profile][key]}")
            for key in credentials[profile]:
                click.echo(f"{key}: {credentials[profile][key]}")
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
    credentials = ctx.obj.get("credentials")
    try:
        for key in config[profile]:
            click.echo(f"{key}: {config[profile][key]}")
        for key in credentials[profile]:
            click.echo(f"{key}: {credentials[profile][key]}")
    except KeyError as err:
        raise click.ClickException("Enter a valid profile name. Run `atko config list` to find the configured profiles.") from err


@cli.command()
@click.option("--profile", "-p", prompt="Enter profile name")
@click.pass_context
def remove(ctx, profile):
    """Remove profile."""

    config_file = ctx.obj.get("config_file")
    credential_file = ctx.obj.get("credential_file")
    cache_file = ctx.obj.get("cache_file")

    config = configparser.ConfigParser()
    config.read(config_file)

    if not config.has_section(profile):
        raise click.ClickException("Enter a valid profile name. Run `atko config list` to find the configured profiles.")

    credential = configparser.ConfigParser()
    credential.read(credential_file)

    with open(cache_file, 'r') as infile:
        oauth_cache = json.load(infile)

    config.remove_section(profile)
    with open(config_file, "w") as cfgfile:
        config.write(cfgfile)

    credential.remove_section(profile)
    with open(credential_file, "w") as credsfile:
        credential.write(credsfile)

    _remove_cache_entry(oauth_cache, profile)
    with open(cache_file, 'w') as outfile:
        json.dump(oauth_cache, outfile)

    click.echo(f"Profile {profile} removed.")


@cli.command()
@click.option("--clear", "-c", is_flag=True, help="Clear cache")
@click.option("--remove", "-r", help="Remove cache entry")
@click.option("--key", "-k", help="Cached profile name")
@click.pass_context
def cache(ctx, clear, remove, key):
    """Access OAuth cache."""

    cache_file = ctx.obj.get("cache_file")
    try:
        with open(cache_file, 'r') as infile:
            oauth_cache = json.load(infile)
        if clear:
            if click.confirm("Clear the OAuth cache?"):
                with open(cache_file, 'w') as outfile:
                    oauth_cache = json.dump({}, outfile)
                click.echo("Cache cleared")
        elif remove is not None:
            if click.confirm("Remove the cache entry?"):
                _remove_cache_entry(oauth_cache, remove)
                with open(cache_file, 'w') as outfile:
                    json.dump(oauth_cache, outfile)
        elif key is not None:
            entry = _get_cache_entry(oauth_cache, key)
            click.echo(json.dumps(entry, indent=4))
        else:
            for cache in oauth_cache:
                click.echo(cache)
    except JSONDecodeError as err:
        raise click.ClickException("Could not access the cache file.") from err


def _get_cache_entry(oauth_cache, key):
    entry = {}
    lst = key.split(":")
    profile = lst[0]
    resource = None
    if (len(lst) == 1):
        entry = oauth_cache.get(profile, {})
    elif (len(lst) == 2):
        resource = lst[1]
        entry = oauth_cache.get(profile, {}).get(resource, {})
    elif (len(lst) == 3):
        resource = lst[1]
        token_type = lst[2]
        entry = oauth_cache.get(profile, {}).get(resource, {}).get(token_type, {})
    else:
        raise click.ClickException("Invalid key.")
    return entry


def _remove_cache_entry(oauth_cache, key):
    entry = {}
    lst = key.split(":")
    profile = lst[0]
    resource = None
    if (len(lst) == 1):
        oauth_cache.pop(profile, {})
    elif (len(lst) == 2):
        resource = lst[1]
        entry = oauth_cache.get(profile, {}).pop(resource, {})
    elif (len(lst) == 3):
        resource = lst[1]
        token_type = lst[2]
        entry = oauth_cache.get(profile, {}).get(resource, {}).pop(token_type, {})
    else:
        raise click.ClickException("Invalid key.")
    return entry


def _create_profile(profile, config_file, credential_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    credentials = configparser.ConfigParser()
    credentials.read(credential_file)

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

        credentials[profile] = _get_token_credentials()

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

        credentials[profile] = _get_oauth_credentials(grant_type)
    else:
        raise click.ClickException(f"Invalid mode {api_mode}")

    with open(config_file, "w") as _config_file:
        config.write(_config_file)

    with open(credential_file, "w") as _credentials_file:
        credentials.write(_credentials_file)


def _get_token_credentials():
    api_token = click.prompt(
        "Enter API Token",
        default=""
    )

    credentials_object = {
        "api_token": api_token,
        "client_id": "",
        "client_secret": "",
        "redirect_uri": "",
        "jwk": "",
        "user_id": "",
        "user_password": ""
    }

    return credentials_object


def _get_oauth_credentials(grant_type):
    CLICK_PROMPT_OAUTH_CLIENT_ID = "Enter OAuth Client ID"
    CLICK_PROMPT_OAUTH_CLIENT_SECRET = "Enter OAuth Client Secret"
    CLICK_PROMPT_OAUTH_REDIRECT_URI = "Enter Redirect URI"
    CLICK_PROMPT_OAUTH_JWK_FILE = "Enter JWK file"

    credentials_object = {}

    if grant_type == "password":
        client_id = click.prompt(
            CLICK_PROMPT_OAUTH_CLIENT_ID,
            default=""
        )

        client_secret = click.prompt(
            CLICK_PROMPT_OAUTH_CLIENT_SECRET,
            default=""
        )

        user_id = click.prompt("Enter Okta User ID")

        user_password = click.prompt("Enter Okta User Password", hide_input=True)

        credentials_object = {
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
            CLICK_PROMPT_OAUTH_CLIENT_ID,
            default=""
        )

        redirect_uri = click.prompt(
            CLICK_PROMPT_OAUTH_REDIRECT_URI,
            default="http://127.0.0.1:12345"
        )

        credentials_object = {
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
            CLICK_PROMPT_OAUTH_CLIENT_ID,
            default=""
        )

        client_secret = click.prompt(
            CLICK_PROMPT_OAUTH_CLIENT_SECRET,
            default=""
        )

        redirect_uri = click.prompt(
            CLICK_PROMPT_OAUTH_REDIRECT_URI,
            default="http://127.0.0.1:12345"
        )

        credentials_object = {
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
            CLICK_PROMPT_OAUTH_CLIENT_ID,
            default=""
        )

        redirect_uri = click.prompt(
            CLICK_PROMPT_OAUTH_REDIRECT_URI,
            default="http://127.0.0.1:12345"
        )

        credentials_object = {
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
            CLICK_PROMPT_OAUTH_CLIENT_ID,
            default=""
        )

        jwk_file = click.prompt(
            CLICK_PROMPT_OAUTH_JWK_FILE,
            default=""
        )

        with open(jwk_file, 'r') as f:
            jwk = json.load(f)

        credentials_object = {
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
    return credentials_object
