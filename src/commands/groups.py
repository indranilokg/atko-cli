import click
import json
import sys
import traceback
from datetime import datetime
from prettytable import PrettyTable
from oktapy.exceptions import ServiceException
from common.okt_common import global_options, get_handler, MutuallyExclusiveOption, DependentOption, timer
import oktapy.manage.GroupMgr as GroupMgr
from oktapy.utils import readCSV


def _multiple_group_from_prompt(prefix, count):
    count = click.prompt(
        "Enter number of groups",
        default=5
    ) if count is None else count

    prefix = click.prompt(
        "Group name prefix",
        default="testrun_"
    ) if prefix is None else prefix

    group_payload = []
    for i in range(count):
        formatted_name = prefix + "group_" + str(i + 1)
        data = {}
        data["profile"] = {
            "name": formatted_name,
            "description": formatted_name
        }

        group_payload.append(data)
    return group_payload


def _single_group_from_prompt(name, description):
    group_name = click.prompt(
        "Group name",
        default="testgroup"
    ) if name is None else name

    group_description = click.prompt(
        "Description",
        default=group_name
    ) if description is None else description

    group_payload = []
    data = {}
    data["profile"] = {
        "name": group_name,
        "description": group_description
    }

    group_payload.append(data)

    print(group_payload)

    return group_payload


def _retrieve_target_ids(groupMgr, query, field="id", file=False, conditions=False, pattern=False):

    if file:
        data = readCSV(query)
        queryField = data.get(field, {})
        if not queryField:
            return []
        queryStr = ",".join(queryField)
    else:
        queryStr = query

    if conditions:
        criteria, p_dict = _get_filter_criteria(query, conditions=conditions, pattern=pattern)
        targets = [group["id"] for group in groupMgr.getGroups(filter=criteria, deepSearch=p_dict)]
    else:
        criteria, p_dict = _get_filter_criteria(queryStr, field)
        targets = [group["id"] for group in groupMgr.getGroups(filter=criteria)]

    print(targets)
    return targets


def _get_filter_criteria(query, field=None, conditions=False, pattern=False):

    p_dict = {}
    criteria = ""

    if conditions:
        if pattern:
            patterns = query.split(",")
            for p in patterns:
                components = p.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid pattern. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                val = components[1]
                p_dict[key] = val
        else:
            condn_list = query.split(",")
            for condn in condn_list:
                components = condn.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid condition. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                if key not in ["id", "type"]:
                    raise click.ClickException(
                        "Only search by id and type supported. To filter based on profile attributes use the [--conditions --pattern] option")
                val = components[1]
                criteria = criteria + f"{key} eq \"{val}\""
                criteria = criteria + " and "
            criteria = criteria[:-5]
    else:
        op = "eq"
        if field in ["id", "type"]:
            search = field
        else:
            raise click.ClickException(
                "Only search by id and type supported. To filter based on profile attributes use the [--conditions --pattern] option")

        keys = query.split(",")
        for key in keys:
            criteria = criteria + f"{search} {op} \"{key}\""
            criteria = criteria + " or "
        criteria = criteria[:-4]
    return criteria, p_dict


def tabulate(itemlist, all=False, mode="stdout", headers=['Name', 'Description', 'Type', "ID"]):
    if mode == "csv":
        item_frame = GroupMgr.to_frame(itemlist)
        click.echo(",".join(item_frame.columns.tolist()))
        csvList = [",".join(item) for item in item_frame.values]
        click.echo("\n".join(csvList))
        click.echo()
        click.echo(f"{len(csvList)} record(s)")
    else:
        t = PrettyTable(headers)

        if all or len(itemlist) <= 10:
            items = [item.summary() for item in itemlist]
        else:
            items = [item.summary() for item in sorted(itemlist[0:5])]
            items = items + [["..." for i in range(len(headers))]] * 2

        for item in items:
            t.add_row(item)
        click.echo(t)
        click.echo(f"{len(itemlist)} record(s)")


@click.group()
def cli():
    """Okta Groups Management"""
    pass


@cli.command(short_help='Get groups based on variety of conditions.')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@click.option('--count', type=int, default=0, help='Maximum number of records to return')
@click.option('--all', '-a', is_flag=True, help='List all records')
@click.option('--multiple', '-m', is_flag=True, help='Search for multiple groups.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--field', default="id", help='Attribute to find groups.', cls=DependentOption, dependent_on=["multiple"])
@click.option('--conditions', '-c', is_flag=True, help='Search based on conditions.', cls=MutuallyExclusiveOption, mutually_exclusive=["multiple"])
@click.option('--pattern', '-e', is_flag=True, help='Search based on pattern or substring. Expensive operation.', cls=DependentOption, dependent_on=["conditions"])  # noqa: E501
@global_options
@click.argument('query')
@click.pass_context
@timer
def get(ctx, output_file, query, count, all, multiple, field, conditions, pattern, **kwargs):
    """Get group"""

    # debug = kwargs["debug"]
    output_mode = kwargs["output"]

    groupMgr = get_handler(ctx, kwargs["profile"], "group")

    if conditions:
        p_dict = {}
        criteria = ""
        if pattern:
            patterns = query.split(",")
            for p in patterns:
                components = p.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid pattern. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                val = components[1]
                p_dict[key] = val
        else:
            condn_list = query.split(",")
            for condn in condn_list:
                components = condn.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid condition. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                if key not in ["id", "type"]:
                    raise click.ClickException(
                        "Only search by id and type supported. To filter based on profile attributes use the [--conditions --pattern] option")
                val = components[1]
                criteria = criteria + f"{key} eq \"{val}\""
                criteria = criteria + " and "
            criteria = criteria[:-5]
        groups_list = groupMgr.getGroups(filter=criteria, threshold=count, deepSearch=p_dict)
    elif multiple:
        if field in ["id", "type"]:
            search = field
        else:
            raise click.ClickException("Only search by id and type supported. To filter based on profile attributes use the [--conditions --pattern] option")
        criteria = ""
        keys = query.split(",")
        for key in keys:
            criteria = criteria + f"{search} eq \"{key}\""
            criteria = criteria + " or "
        criteria = criteria[:-4]
        groups_list = groupMgr.getGroups(filter=criteria, threshold=count)
    else:
        key = query
        group = groupMgr.getGroup(key)
        groups_list = [group]

    if(output_file):
        if output_mode == "csv":
            GroupMgr.to_frame(groups_list).to_csv(output_file.name, index=False)
        else:
            json.dump([json.loads(str(ob)) for ob in groups_list], output_file, indent=4, sort_keys=True)
        click.echo(f"Saved groups in {output_file.name}")
    elif output_mode == "id":
        click.echo(','.join([group["id"] for group in groups_list]))
    elif output_mode == "name":
        click.echo(','.join([group["profile"]["name"] for group in groups_list]))
    elif output_mode == "json":
        click.echo(groups_list)
    elif output_mode == "csv":
        tabulate(groups_list, all=True, mode="csv")
    else:
        tabulate(groups_list, all=all)


@cli.command(short_help='List Groups')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@click.option('--all', '-a', is_flag=True, help='List all records')
@click.option('--query', '-q', help='Matches the specified query against first name, last name, or email', cls=MutuallyExclusiveOption, mutually_exclusive=["filter"])  # noqa: E501
@click.option('--filter', '-f', help='Matches with the filter criteria', cls=MutuallyExclusiveOption, mutually_exclusive=["query"])
@click.option('--count', type=int, default=0, help='Maximum number of records to return')
@click.option('--pattern', '-e', help='Search based on pattern or substring. Expensive operation.')
@global_options
@click.pass_context
@timer
def find(ctx, output_file, all, query, filter, count, pattern, **kwargs):
    """List all groups. Optionally save them to a file."""

    debug = kwargs["debug"]
    output_mode = kwargs["output"]

    groupMgr = get_handler(ctx, kwargs["profile"], "group")
    try:
        p_dict = {}
        if pattern:
            patterns = pattern.split(",")
            for p in patterns:
                components = p.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid pattern. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                val = components[1]
                p_dict[key] = val

        groups_list = groupMgr.getGroups(query=query, filter=filter, threshold=count, deepSearch=p_dict)
    except ServiceException as ex:
        click.echo(traceback.format_exc()) if debug else click.echo(f"Error: {ex.info}")
        click.echo()
        sys.exit(113)
    except Exception as ex:
        click.echo(traceback.format_exc()) if debug else click.echo(f"Error: {ex}")
        click.echo()
        sys.exit(113)
    else:
        if(output_file):
            if output_mode == "csv":
                GroupMgr.to_frame(groups_list).to_csv(output_file.name, index=False)
            else:
                json.dump([json.loads(str(ob)) for ob in groups_list], output_file, indent=4, sort_keys=True)
            click.echo(f"Saved groups in {output_file.name}")
        elif output_mode == "id":
            click.echo(','.join([group["id"] for group in groups_list]))
        elif output_mode == "name":
            click.echo(','.join([group["profile"]["name"] for group in groups_list]))
        elif output_mode == "json":
            click.echo(groups_list)
        elif output_mode == "csv":
            tabulate(groups_list, all=True, mode="csv")
        else:
            tabulate(groups_list, all=all)
        click.echo()


@cli.command(short_help='Delete Groups')
@global_options
@click.option('--confirm', '-y', is_flag=True, help='Confirm operation.')
@click.option('--field', default="id", help='Attribute to find groups.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--file', '-f', is_flag=True, help='Header based CSV file containing target groups.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])  # noqa: E501
@click.option('--conditions', '-c', is_flag=True, help='Search based on conditions.', cls=MutuallyExclusiveOption, mutually_exclusive=["file", "field"])  # noqa: E501
@click.option('--pattern', '-e', is_flag=True, help='Search based on pattern or substring. Expensive operation.', cls=DependentOption, dependent_on=["conditions"])  # noqa: E501
@click.argument('query')
@click.pass_context
@timer
def delete(ctx, query, confirm, field, file, conditions, pattern, **kwargs):
    """Delete groups."""

    success = []
    failure = []
    debug = kwargs["debug"]

    groupMgr = get_handler(ctx, kwargs["profile"], "group")

    try:
        targets = _retrieve_target_ids(groupMgr,
                                       query=query,
                                       field=field,
                                       file=file,
                                       conditions=conditions,
                                       pattern=pattern)
    except ServiceException as ex:
        click.echo(traceback.format_exc()) if debug else click.echo(f"Error: {ex.info}")
        sys.exit(113)
    except Exception as ex:
        click.echo(traceback.format_exc()) if debug else click.echo(f"Error: {ex}")
        sys.exit(113)
    else:
        if len(targets) == 0:
            click.echo("No target groups(s) to delete.")
            sys.exit(0)

        if confirm or click.confirm(f"{len(targets)} groups(s) are going to be deleted. Proceed?"):
            result = groupMgr.deleteGroups(targets)
            success = result["success"]
            failure = result["failure"]
            datestr = datetime.now().strftime("%Y%m%d-%H%M%S")

            click.echo(f"{len(success)} groups(s) successfully deleted.")
            if len(success) > 0:
                successFile = "okt_group_delete_success_" + datestr + ".txt"
                with open(successFile, 'w') as outfile:
                    json.dump(success, outfile)
            if len(failure) > 0:
                click.echo(f"Deletion failed for {len(failure)} group(s).")
                failureFile = "okt_group_delete_failed_" + datestr + ".txt"
                with open(failureFile, 'w') as outfile:
                    json.dump(failure, outfile)

            if debug:
                errors = result["errors"]
                if len(errors) > 0:
                    errorFile = "okt_errors_group_delete_" + datestr + ".log"
                    with open(errorFile, 'w') as outfile:
                        json.dump(errors, outfile)
                        click.echo(f"Error information saved to {errorFile}")
        else:
            click.echo("Cancelled.")

    click.echo()


@cli.command(short_help='Create groups')
@global_options
@click.option('--multiple', '-m', is_flag=True, help='Create multiple groups', cls=MutuallyExclusiveOption, mutually_exclusive=["input_file", "name", "description"])
@click.option('--name', help='Group name', cls=MutuallyExclusiveOption, mutually_exclusive=["multiple", "input_file"])
@click.option('--description', help='Group description', cls=MutuallyExclusiveOption, mutually_exclusive=["multiple", "input_file"])
@click.option('--prefix', help='Group name prefix', cls=DependentOption, dependent_on=["multiple"])
@click.option('--count', type=int, help='Number of groups', cls=DependentOption, dependent_on=["multiple"])
@click.option('--file', '-f', 'input_file', help='Input file', cls=MutuallyExclusiveOption, mutually_exclusive=["multiple", "name", "description"])
@click.option('--mode', default='json', help='Group paylod format (JSON or CSV)', cls=DependentOption, dependent_on=["input_file"])
@click.pass_context
@timer
def create(ctx, multiple, name, description, prefix, count, input_file, mode, **kwargs):
    """Create groups."""

    debug = kwargs["debug"]

    group_payload = []

    if input_file is None:
        group_payload = _multiple_group_from_prompt(prefix, count) \
            if multiple \
            else _single_group_from_prompt(name, description)

    groupMgr = get_handler(ctx, kwargs["profile"], "group")
    result = groupMgr.createGroups(inputs=group_payload, file=input_file, mode=mode)

    success = result["success"]
    failure = result["failure"]
    datestr = datetime.now().strftime("%Y%m%d-%H%M%S")

    click.echo(f"{len(success)} groups(s) successfully created.")

    if len(success) > 0:
        successFile = "okt_group_create_success_" + datestr + ".txt"
        with open(successFile, 'w') as outfile:
            json.dump(success, outfile)

    if len(failure) > 0:
        click.echo(f"Creation failed for {len(failure)} group(s).")

    if debug:
        errors = []
        if result:
            errors = errors + result["errors"]

            if len(failure) > 0:
                failureFile = "okt_group_create_failed_" + datestr + ".txt"
                with open(failureFile, 'w') as outfile:
                    json.dump(failure, outfile)

            if len(errors) > 0:
                errorFile = "okt_errors_group_create_" + datestr + ".log"
                with open(errorFile, 'w') as outfile:
                    json.dump(errors, outfile)
                    click.echo(f"Error information saved to {errorFile}")

    click.echo()
