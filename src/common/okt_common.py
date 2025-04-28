import click
import functools
import time
from click import Option, UsageError
from oktapy.okta import Okta

_global_options = [
    click.option('--profile', '-p', default="DEFAULT", envvar='ATKO_PROFILE', help='Profile name'),
    click.option('--debug', is_flag=True, help="Debug information on Exceptions"),
    click.option('--verbose', '-v', is_flag=True, help="Show API calls as cURL commands"),
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
    _provider = Okta(_profile["base_url"], token=_profile["api_token"], verbose=ctx.params.get("verbose", False))
    return _provider


def get_handler(ctx, profilename, resource):
    _profile = get_profile(ctx, profilename)
    _provider = Okta(_profile["base_url"], token=_profile["api_token"], verbose=ctx.params.get("verbose", False))
    if resource == "users":
        return _provider.UserMgr()
    elif resource == "groups":
        return _provider.GroupMgr()
    else:
        raise click.ClickException(f"Invalid resource {resource}")
