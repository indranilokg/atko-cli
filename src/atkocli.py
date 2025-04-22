import click
import os
import sys
import json
import configparser
import importlib.util

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class AtkoCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith('__init__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            module_path = os.path.join(plugin_folder, name + '.py')
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.cli
        except Exception as e:
            click.echo(f"Error loading command {name}: {str(e)}", err=True)
            return None

    def __call__(self, *args, **kwargs):
        try:
            return super(AtkoCLI, self).__call__(
                *args, standalone_mode=False, **kwargs)
        except click.exceptions.UsageError as ex:
            ex.ctx = None
            click.echo(f"Error: {ex.message}")
            click.echo()
            try:
                super(AtkoCLI, self).__call__(['--help'])
            except SystemExit:
                sys.exit(ex.exit_code)
        except click.exceptions.ClickException as ex:
            ex.ctx = None
            click.echo(f"Error: {ex.message}")
            click.echo()
            sys.exit(111)
        except Exception as ex:
            ex.ctx = None
            ex.exit_code = 111
            click.echo(f"{ex.__class__}:{ex}")
            click.echo()
            sys.exit(112)


@click.command(cls=AtkoCLI, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    """CLI tool for your Okta org."""

    _config_directory = os.path.expanduser("~/.atkocli")
    _config_file = os.path.expanduser(_config_directory + "/config")
    _credential_file = os.path.expanduser(_config_directory + "/credentials")
    _cache_file = os.path.expanduser(_config_directory + "/cache")

    if(not os.path.isdir(_config_directory)):
        click.echo(f"{_config_directory} does not exist")
        try:
            os.mkdir(os.path.expanduser(_config_directory))
        except OSError:
            click.echo(f"Creation of the directory {_config_directory} failed")
            raise
        else:
            click.echo(f"Successfully created the directory {_config_directory}")

    _config = configparser.ConfigParser()
    _credentials = configparser.ConfigParser()

    if os.path.exists(_config_file):
        _config.read(_config_file)
    else:
        with open(_config_file, 'w'):
            _config.write(_config_file)

    if os.path.exists(_credential_file):
        _credentials.read(_credential_file)
    else:
        with open(_credential_file, 'w'):
            _credentials.write(_credential_file)

    if not os.path.exists(_cache_file):
        with open(_cache_file, 'w') as out:
            json.dump({}, out)

    ctx.obj = {
        'config': _config,
        'credentials': _credentials,
        'config_file': _config_file,
        'credential_file': _credential_file,
        'cache_file': _cache_file
    }


if __name__ == '__main__':
    cli()
