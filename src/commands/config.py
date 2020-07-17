import click
import os
import json


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Store configuration values."""

    if ctx.invoked_subcommand is None:
        config_file = os.path.expanduser('~/.okt.cfg')

        base_url = click.prompt(
            "Enter Okta Org URL",
            default=ctx.obj.get('base_url', 'https://example.okta.com')
        )

        api_token = click.prompt(
            "Enter API Token",
            default=ctx.obj.get('api_token', '')
        )

        config = {
            'api_token': api_token,
            'base_url': base_url
        }

        with open(config_file, 'w') as cfg:
            cfg.write(json.dumps(config))


@cli.command()
@click.pass_context
def list(ctx):
    """Show current profile."""

    api_token = ctx.obj['api_token']
    base_url = ctx.obj['base_url']
    print(f"base_url={base_url}")
    print(f"api_token={api_token}")
