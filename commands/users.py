import click
import json
from oktapy.okta import Okta


@click.group()
def cli():
    """Okta User Management"""

    pass


@cli.command(short_help='Get cuurent user')
@click.pass_context
def current(ctx):
    """Get cuurent user."""

    userMgr = Okta(ctx.obj.get('base_url'), token=ctx.obj.get('api_token')).UserMgr()
    currentUser = userMgr.getCurrentUser()
    print(currentUser.profile["login"])
    print(currentUser.profile)


@cli.command(short_help='List all users')
@click.option('-f', '--file', 'output_file', type=click.File(mode="w"), help='Output JSON file')
@click.pass_context
def list(ctx, output_file):
    """List all users. Optionally save them to a file."""

    userMgr = Okta(ctx.obj.get('base_url'), token=ctx.obj.get('api_token')).UserMgr()
    users_list = userMgr.getUsers()

    if(output_file):
        json.dump([json.loads(str(ob)) for ob in users_list], output_file, indent=4, sort_keys=True)
        click.echo(f"Saved users in {output_file.name}")
    else:
        print(users_list)


@cli.command(short_help='Create a single user')
@click.option('-f', '--file', 'input_file', type=click.File(), help='Input JSON file')
@click.pass_context
def create(ctx, input_file):
    """Create a single user from input or a json file."""

    # userMgr = Okta(ctx.obj.get('base_url'), token=ctx.obj.get('api_token')).UserMgr()

    if(input_file):
        click.echo(f"Creating users from {input_file.name}")
    else:
        click.echo("Creating users from input")


@cli.command(short_help='Delete a single user')
@click.argument('userid')
@click.pass_context
def delete(ctx, userid):
    """Delete a single user.

    USERID login or internal ID.
    """
    userMgr = Okta(ctx.obj.get('base_url'), token=ctx.obj.get('api_token')).UserMgr()
    user = userMgr.getUser(userid)
    print(user.id)

    click.echo(f"Deleting user {userid}")
    result = userMgr.deleteUser(user.id)
    print(result)
