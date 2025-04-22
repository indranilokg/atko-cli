import click
import sys
import os
import json
import traceback
from prettytable import PrettyTable

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.okt_common import global_options, get_profile, get_okta_provider
from oktapy.okta import Okta
from oktapy.manage.GroupMgr import GroupMgr
from oktapy.manage.UserMgr import UserMgr
from oktapy.exceptions import ServiceException
from oktapy.resources.user import User  # Add this import at the top

@click.group()
@global_options
@click.pass_context
def cli(ctx, **kwargs):
    """Okta Group Management"""
    pass

def tabulate(itemlist, all=False, mode="stdout", headers=['Name', 'Type', 'ID']):
    if mode == "csv":
        item_frame = GroupMgr.to_frame(itemlist)
        click.echo(",".join(item_frame.columns.tolist()))
        csv_list = [",".join(item) for item in item_frame.values]
        click.echo("\n".join(csv_list))
        click.echo()
        click.echo(f"{len(csv_list)} record(s)")
    else:
        _pretty_table = PrettyTable(headers)

        if all or len(itemlist) <= 10:
            items = [[item["profile"]["name"], item["type"], item["id"]] for item in itemlist]
        else:
            items = [[item["profile"]["name"], item["type"], item["id"]] for item in sorted(itemlist[0:5])]
            items = items + [["..." for i in range(len(headers))]] * 2

        for item in items:
            _pretty_table.add_row(item)
        click.echo(_pretty_table)
        click.echo(f"{len(itemlist)} record(s)")

@cli.command()
@click.option('--query', help='Search query for group name')
@click.option('--filter', help='Filter expression for groups')
@click.option('--limit', type=int, default=20, help='Number of results to return')
@click.option('--all', '-a', is_flag=True, help='List all records')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@global_options
@click.pass_context
def find(ctx, query, filter, limit, all, output_file, **kwargs):
    """List groups"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        groups = provider.GroupMgr().list(query=query, filter=filter, limit=limit)
        output_mode = kwargs.get("output", "stdout")
        
        if output_file:
            if output_mode == "csv":
                GroupMgr.to_frame(groups).to_csv(output_file.name, index=False)
            else:
                json.dump([json.loads(str(group)) for group in groups], output_file, indent=4, sort_keys=True)
            click.echo(f"Saved groups in {output_file.name}")
        elif output_mode == "id":
            click.echo(','.join([group["id"] for group in groups]))
        elif output_mode == "json":
            click.echo(groups)
        elif output_mode == "csv":
            tabulate(groups, all=True, mode="csv")
        else:
            tabulate(groups, all=all)
            
    except ServiceException as e:
        click.echo(f"Error listing groups: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error listing groups: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error listing groups: {str(e)}")

def _group_from_prompt():
    """Interactive group creation helper"""
    click.echo("Please provide the following information:")
    name = click.prompt("Group name", type=str)
    
    if click.confirm("Do you want to add a description?", default=True):
        description = click.prompt("Description", type=str, default="")
    else:
        description = ""
        
    return {
        'profile': {
            'name': name,
            'description': description
        }
    }

@cli.command()
@click.option('--name', help='Name of the group')
@click.option('--description', help='Description of the group')
@click.option('--no-input', is_flag=True, help='Non-interactive mode, requires --name option')
@global_options
@click.pass_context
def create(ctx, name, description, no_input, **kwargs):
    """Create a new group"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        # If name is provided or no-input is set, use non-interactive mode
        if name is not None or no_input:
            if not name:
                click.echo("Error: Group name is required in non-interactive mode")
                click.echo("Either provide --name option or use interactive mode")
                return
            group_data = {
                'profile': {
                    'name': name
                }
            }
            if description:
                group_data['profile']['description'] = description
        else:
            # Interactive mode only if no name provided
            group_data = _group_from_prompt()
        
        group = provider.GroupMgr().create(group_data)
        if not group:
            click.echo("Failed to create group")
            return
            
        output_mode = kwargs.get("output", "stdout")
        
        if output_mode == "id":
            click.echo(group["id"])
        elif output_mode == "json":
            click.echo(json.dumps(group, indent=2))
        else:
            # Show the created group in table format
            tabulate([group], all=True)
            click.echo(f"\nGroup '{group_data['profile']['name']}' created successfully with ID: {group['id']}")
            
    except ServiceException as e:
        click.echo(f"Error creating group: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error creating group: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error creating group: {str(e)}")

@cli.command()
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@global_options
@click.argument('id')
@click.pass_context
def get(ctx, id, output_file, **kwargs):
    """Get group details"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        group = provider.GroupMgr().get(id)
        output_mode = kwargs.get("output", "stdout")
        
        if output_file:
            if output_mode == "csv":
                GroupMgr.to_frame([group]).to_csv(output_file.name, index=False)
            else:
                json.dump(json.loads(str(group)), output_file, indent=4, sort_keys=True)
            click.echo(f"Saved group in {output_file.name}")
        elif output_mode == "id":
            click.echo(group["id"])
        elif output_mode == "json":
            click.echo(group)
        elif output_mode == "csv":
            tabulate([group], all=True, mode="csv")
        else:
            tabulate([group], all=True)
            
    except ServiceException as e:
        click.echo(f"Error getting group: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error getting group: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error getting group: {str(e)}")

@cli.command()
@global_options
@click.argument('id')
@click.option('--force', '-f', is_flag=True, help='Delete without confirmation')
@click.pass_context
def delete(ctx, id, force, **kwargs):
    """Delete a group"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        if not force:
            # Get group details first to show what's being deleted
            group = provider.GroupMgr().get(id)
            if not click.confirm(f"Are you sure you want to delete group '{group['profile']['name']}' ({id})?"):
                click.echo("Operation cancelled")
                return

        result = provider.GroupMgr().delete(id)
        if result:
            click.echo(f"Group {id} deleted successfully")
        else:
            click.echo(f"Failed to delete group {id}")
    except ServiceException as e:
        click.echo(f"Error deleting group: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error deleting group: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error deleting group: {str(e)}")

@cli.group()
def users():
    """Manage group members"""
    pass

@users.command(name='list')
@click.option('--group-id', required=True, help='Group ID')
@click.option('--limit', type=int, default=200, help='Number of results to return')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@click.option('--all', '-a', is_flag=True, help='List all records')
@global_options
@click.pass_context
def list_users(ctx, group_id, limit, output_file, all, **kwargs):
    """List group members"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        raw_users = provider.GroupMgr().list_users(group_id, limit=limit)
        # Convert raw user data to User objects
        users = [User(data) for data in raw_users]
        
        output_mode = kwargs.get("output", "stdout")
        
        if output_file:
            if output_mode == "csv":
                UserMgr.to_frame(users).to_csv(output_file.name, index=False)
            else:
                json.dump([json.loads(str(user)) for user in users], output_file, indent=4, sort_keys=True)
            click.echo(f"Saved users in {output_file.name}")
        elif output_mode == "id":
            click.echo(','.join([user["id"] for user in users]))
        elif output_mode == "json":
            click.echo(users)
        elif output_mode == "csv":
            tabulate(users, all=True, mode="csv", headers=['Login', 'First Name', 'Last Name', 'Email', 'Status', 'ID'])
        else:
            if all or len(users) <= 10:
                items = [user.summary() for user in users]
            else:
                items = [user.summary() for user in sorted(users[0:5])]
                items = items + [["..." for i in range(6)]] * 2

            _pretty_table = PrettyTable(['Login', 'First Name', 'Last Name', 'Email', 'Status', 'ID'])
            for item in items:
                _pretty_table.add_row(item)
            click.echo(_pretty_table)
            click.echo(f"{len(users)} record(s)")
            
    except ServiceException as e:
        click.echo(f"Error listing users: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error listing users: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error listing users: {str(e)}")

@users.command(name='add')
@click.option('--group-id', required=True, help='Group ID')
@click.option('--user-id', required=True, help='User ID')
@global_options
@click.pass_context
def add_user(ctx, group_id, user_id, **kwargs):
    """Add user to group"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    debug = kwargs.get("debug", False)
    try:
        # First verify the group exists
        try:
            group = provider.GroupMgr().get(group_id)
            if not group:
                click.echo(f"Error: Group {group_id} not found")
                return
        except Exception as e:
            click.echo(f"Error: Group {group_id} not found")
            if debug:
                click.echo(str(e))
            return

        # Then verify the user exists
        try:
            user = provider.UserMgr().getUser(user_id)
            if not user:
                click.echo(f"Error: User {user_id} not found")
                return
        except Exception as e:
            click.echo(f"Error: User {user_id} not found")
            if debug:
                click.echo(str(e))
            return

        # If both exist, try to add the user to the group
        result = provider.GroupMgr().add_user(group_id, user_id)
        # 204 status code or True both indicate success
        if result == 204 or result is True:
            click.echo(f"User {user_id} ({user['profile']['login']}) added to group {group_id} ({group['profile']['name']})")
        else:
            if debug:
                click.echo(f"Unexpected response: {result}")
            click.echo(f"Failed to add user {user_id} to group {group_id}")
    except ServiceException as e:
        click.echo(f"Error adding user: {str(e)}")
    except Exception as e:
        if debug:
            click.echo(f"Error adding user: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error adding user: {str(e)}")

@users.command(name='remove')
@click.option('--group-id', required=True, help='Group ID')
@click.option('--user-id', required=True, help='User ID')
@global_options
@click.pass_context
def remove_user(ctx, group_id, user_id, **kwargs):
    """Remove user from group"""
    provider = get_okta_provider(ctx, kwargs["profile"])
    try:
        provider.GroupMgr().remove_user(group_id, user_id)
        click.echo(f"User {user_id} removed from group {group_id}")
    except ServiceException as e:
        click.echo(f"Error removing user: {str(e)}")
    except Exception as e:
        if kwargs["debug"]:
            click.echo(f"Error removing user: {str(e)}")
            traceback.print_exc()
        else:
            click.echo(f"Error removing user: {str(e)}") 