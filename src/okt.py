import click
import os
import sys
import json
import configparser

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class OktaCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith('__init__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        try:
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
        except Exception as e:
            print(e)
            pass
        else:
            return ns['cli']

    def __call__(self, *args, **kwargs):
        try:
            return super(OktaCLI, self).__call__(
                *args, standalone_mode=False, **kwargs)
        except click.exceptions.UsageError as ex:
            ex.ctx = None
            click.echo(f"Error: {ex.message}")
            click.echo()
            try:
                super(OktaCLI, self).__call__(['--help'])
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
            # raise


@click.command(cls=OktaCLI, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    """CLI tool for your Okta org."""

    configDir = os.path.expanduser("~/.okt")
    configfile = os.path.expanduser(configDir + "/config")
    credsfile = os.path.expanduser(configDir + "/credentials")
    cahcefile = os.path.expanduser(configDir + "/cache")

    if(not os.path.isdir(configDir)):
        click.echo(f"{configDir} does not exist")
        try:
            os.mkdir(os.path.expanduser(configDir))
        except OSError:
            click.echo(f"Creation of the directory {configDir} failed")
            raise
        else:
            click.echo(f"Successfully created the directory {configDir}")

    config = configparser.ConfigParser()
    creds = configparser.ConfigParser()

    if os.path.exists(configfile):
        config.read(configfile)
    else:
        with open(configfile, 'w'):
            config.write(configfile)

    if os.path.exists(credsfile):
        creds.read(credsfile)
    else:
        with open(credsfile, 'w'):
            creds.write(credsfile)

    if not os.path.exists(cahcefile):
        with open(cahcefile, 'w') as out:
            json.dump({}, out)

    ctx.obj = {
        'config': config,
        'creds': creds,
        'config_file': configfile,
        'creds_file': credsfile,
        'cache_file': cahcefile
    }


if __name__ == '__main__':
    cli()
