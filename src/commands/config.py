import click
import configparser


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

    config = configparser.ConfigParser()
    config.read(config_file)

    if not config.has_section(profile):
        raise click.ClickException("Enter a valid profile name. Run `atko config list` to find the configured profiles.")

    credential = configparser.ConfigParser()
    credential.read(credential_file)

    config.remove_section(profile)
    with open(config_file, "w") as cfgfile:
        config.write(cfgfile)

    credential.remove_section(profile)
    with open(credential_file, "w") as credsfile:
        credential.write(credsfile)

    click.echo(f"Profile {profile} removed.")


def _create_profile(profile, config_file, credential_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    credentials = configparser.ConfigParser()
    credentials.read(credential_file)

    base_url = click.prompt(
        "Enter Okta Org URL",
        default="https://example.okta.com"
    )

    config[profile] = {
        "base_url": base_url,
        "api_mode": "token"
    }

    api_token = click.prompt(
        "Enter API Token",
        default=""
    )

    credentials[profile] = {
        "api_token": api_token
    }

    with open(config_file, "w") as _config_file:
        config.write(_config_file)

    with open(credential_file, "w") as _credentials_file:
        credentials.write(_credentials_file)
