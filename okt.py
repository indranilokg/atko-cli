import click
import os
import json

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
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.command(cls=OktaCLI, context_settings=CONTEXT_SETTINGS)
@click.option(
    '--config-file', '-c',
    type=click.Path(),
    default='~/.okt.cfg',
)
@click.pass_context
def cli(ctx, config_file):
    """CLI tool for your Okta org."""
    filename = os.path.expanduser(config_file)

    if os.path.exists(filename):
        with open(filename) as cfg:
            config = json.loads(cfg.read())
        ctx.obj = {
            'base_url': config['base_url'],
            'api_token': config['api_token'],
            'config_file': filename
        }
    else:
        ctx.obj = {
            'config_file': filename
        }


if __name__ == '__main__':
    cli()
