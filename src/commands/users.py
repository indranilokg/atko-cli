import click
import json
import sys
import traceback
from datetime import datetime
from prettytable import PrettyTable
from oktapy.exceptions import ServiceException
from common.okt_common import global_options, get_handler, MutuallyExclusiveOption, DependentOption, timer
import oktapy.manage.UserMgr as UserMgr
from oktapy.utils import readCSV


def _multiple_user_from_prompt(password=None, password_import=False, password_required=True):
    count = click.prompt(
        "Enter number of users",
        default=5
    )

    domain = click.prompt(
        "Email domain",
        default="example.com"
    )

    prefix = click.prompt(
        "Login prefix",
        default="testrun_"
    )

    if password_required:
        password = click.prompt(
            "Default password",
            hide_input=True
        ) if password is None else password

    user_payload = []
    for i in range(count):
        formatted_login = prefix + "user" + str(i + 1) + "@" + domain
        data = {}
        data["profile"] = {
            "firstName": prefix + "user" + str(i + 1),
            "lastName": "oktgen",
            "email": formatted_login,
            "login": formatted_login
        }
        if password_required:
            data["credentials"] = {
                "password": {"value": password},
            }
        elif password_import:
            data["credentials"] = {
                "password": {"hook": {"type": "default"}},
            }

        user_payload.append(data)
    return user_payload


def _single_user_from_prompt(password=None, password_import=False, password_required=True):
    user_login = click.prompt(
        "Login",
        default="testuser@example.com"
    )

    user_email = click.prompt(
        "Email",
        default=user_login
    )

    user_firstname = click.prompt(
        "First Name"
    )

    user_lastname = click.prompt(
        "Last Name"
    )

    if password_required:
        user_password = click.prompt(
            "Password",
            hide_input=True
        ) if password is None else password

    user_payload = []
    data = {}
    data["profile"] = {
        "firstName": user_firstname,
        "lastName": user_lastname,
        "email": user_email,
        "login": user_login
    }

    if password_required:
        data["credentials"] = {
            "password": {"value": user_password},
        }
    elif password_import:
        data["credentials"] = {
            "password": {"hook": {"type": "default"}},
        }

    user_payload.append(data)

    print(user_payload)

    return user_payload


def _retrieve_target_ids(userMgr, query, operation=None, field="id", prefix=False, file=False, conditions=False, pattern=False):

    ALL_STATUS = ["STAGED", "PROVISIONED", "ACTIVE", "RECOVERY", "LOCKED_OUT", "PASSWORD_EXPIRED", "SUSPENDED", "DEPROVISIONED"]

    if operation == "deactivate":
        statusList = list(set(ALL_STATUS) - {"DEPROVISIONED"})
    elif operation == "delete":
        statusList = ["DEPROVISIONED"]
    else:
        statusList = ALL_STATUS

    if file:
        data = readCSV(query)
        queryField = data.get(field, {})
        if not queryField:
            return []
        queryStr = ",".join(queryField)
    else:
        queryStr = query

    if conditions:
        criteria, p_dict = _get_filter_criteria(query, conditions=conditions, pattern=pattern, statusList=statusList)
        targets = [user["id"] for user in userMgr.getUsers(search=criteria, deepSearch=p_dict)]
    else:
        criteria, p_dict = _get_filter_criteria(queryStr, field, statusList=statusList, fuzzy=prefix)
        targets = [user["id"] for user in userMgr.getUsers(search=criteria)]

    print(targets)
    return targets


def _get_filter_criteria(query, field=None, statusList=[], conditions=False, pattern=False, fuzzy=False):

    p_dict = {}
    criteria = ""
    statusFilter = ""

    if len(statusList) > 0:
        for status in statusList:
            statusFilter = statusFilter + f"status eq \"{status}\""
            statusFilter = statusFilter + " or "
        statusFilter = statusFilter[:-4]
        statusFilter = "(" + statusFilter + ")"

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
                criteria = statusFilter
        else:
            condn_list = query.split(",")
            for condn in condn_list:
                components = condn.split(":")
                if len(components) != 2:
                    raise click.ClickException("Invalid condition. Use `key1:value1[,key2:value2,...]` format.")
                key = components[0]
                if key not in ["id", "status", "type.id"]:
                    key = "profile." + key
                val = components[1]
                criteria = criteria + f"{key} sw \"{val}\""
                criteria = criteria + " and "
            criteria = criteria[:-5]
            if len(statusList) > 0:
                criteria = "(" + criteria + ") and " + statusFilter
    else:
        op = "sw" if fuzzy else "eq"
        if field in ["id", "status", "type.id"]:
            search = field
        else:
            search = f"profile.{field}"

        keys = query.split(",")
        for key in keys:
            criteria = criteria + f"{search} {op} \"{key}\""
            criteria = criteria + " or "
        criteria = criteria[:-4]
        if len(statusList) > 0:
            criteria = "(" + criteria + ") and " + statusFilter
    return criteria, p_dict


def tabulate(itemlist, all=False, mode="stdout", headers=['Login', 'First Name', 'Last Name', 'Email', "Status", "ID"]):
    if mode == "csv":
        item_frame = UserMgr.to_frame(itemlist)
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
    """Okta User Management"""
    pass


@cli.command(short_help='Get current user')
@click.option('--attr', help='Filter with subset of attributes')
@global_options
@click.pass_context
@timer
def current(ctx, attr, **kwargs):
    """Get current user"""

    output_mode = kwargs["output"]

    userMgr = get_handler(ctx, kwargs["profile"], "user")
    currentUser = userMgr.getCurrentUser(attr=attr)
    if output_mode == "id":
        click.echo(currentUser["id"])
    elif output_mode == "login":
        click.echo(currentUser["profile"]["login"])
    elif output_mode == "json":
        click.echo(currentUser)
    elif output_mode == "csv":
        tabulate([currentUser], all=True, mode="csv")
    else:
        tabulate([currentUser])


@cli.command(short_help='Fetch details of a single user by ID, Login or Login Shortname.')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@click.option('--attr', help='Filter with subset of attributes')
@click.option('--count', type=int, default=0, help='Maximum number of records to return')
@click.option('--all', '-a', is_flag=True, help='List all records')
@click.option('--multiple', '-m', is_flag=True, help='Search for multiple users.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--field', default="login", help='Attribute to find users.', cls=DependentOption, dependent_on=["multiple"])
@click.option('--conditions', '-c', is_flag=True, help='Search based on conditions.', cls=MutuallyExclusiveOption, mutually_exclusive=["multiple"])
@click.option('--pattern', '-e', is_flag=True, help='Search based on pattern or substring. Expensive operation.', cls=DependentOption, dependent_on=["conditions"])  # noqa: E501
@global_options
@click.argument('query')
@click.pass_context
@timer
def get(ctx, output_file, query, attr, count, all, multiple, field, conditions, pattern, **kwargs):
    """Get user"""

    # debug = kwargs["debug"]
    output_mode = kwargs["output"]

    userMgr = get_handler(ctx, kwargs["profile"], "user")

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
                if key not in ["id", "status", "type.id"]:
                    key = "profile." + key
                val = components[1]
                criteria = criteria + f"{key} sw \"{val}\""
                criteria = criteria + " and "
            criteria = criteria[:-5]
        users_list = userMgr.getUsers(search=criteria, attr=attr, threshold=count, deepSearch=p_dict)
    elif multiple:
        if field in ["id", "status", "type.id"]:
            search = field
        else:
            search = f"profile.{field}"
        criteria = ""
        keys = query.split(",")
        for key in keys:
            criteria = criteria + f"{search} sw \"{key}\""
            criteria = criteria + " or "
        criteria = criteria[:-4]
        users_list = userMgr.getUsers(search=criteria, attr=attr, threshold=count)
    else:
        key = query
        user = userMgr.getUser(key, attr=attr)
        users_list = [user]

    if(output_file):
        if output_mode == "csv":
            UserMgr.to_frame(users_list).to_csv(output_file.name, index=False)
        else:
            json.dump([json.loads(str(ob)) for ob in users_list], output_file, indent=4, sort_keys=True)
        click.echo(f"Saved users in {output_file.name}")
    elif output_mode == "id":
        click.echo(','.join([user["id"] for user in users_list]))
    elif output_mode == "login":
        click.echo(','.join([user["profile"]["login"] for user in users_list]))
    elif output_mode == "json":
        click.echo(users_list)
    elif output_mode == "csv":
        tabulate(users_list, all=True, mode="csv")
    else:
        tabulate(users_list, all=all)


@cli.command(short_help='List users')
@click.option('--file', 'output_file', type=click.File(mode="w"), help='Output file')
@click.option('--all', '-a', is_flag=True, help='List all records')
@click.option('--query', '-q', help='Matches the specified query against first name, last name, or email', cls=MutuallyExclusiveOption, mutually_exclusive=["filter", "search"])  # noqa: E501
@click.option('--filter', '-f', help='Matches with the filter criteria', cls=MutuallyExclusiveOption, mutually_exclusive=["query", "search"])
@click.option('--search', '-s', help='Searches based on criteria', cls=MutuallyExclusiveOption, mutually_exclusive=["query", "filter"])
@click.option('--attr', help='Filter with subset of attributes')
@click.option('--count', type=int, default=0, help='Maximum number of records to return')
@click.option('--pattern', '-e', help='Search based on pattern or substring. Expensive operation.')
@global_options
@click.pass_context
@timer
def find(ctx, output_file, all, query, filter, search, attr, count, pattern, **kwargs):
    """List all users. Optionally save them to a file."""

    debug = kwargs["debug"]
    output_mode = kwargs["output"]

    userMgr = get_handler(ctx, kwargs["profile"], "user")
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

        users_list = userMgr.getUsers(query=query, filter=filter, search=search, attr=attr, threshold=count, deepSearch=p_dict)
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
                UserMgr.to_frame(users_list).to_csv(output_file.name, index=False)
            else:
                json.dump([json.loads(str(ob)) for ob in users_list], output_file, indent=4, sort_keys=True)
            click.echo(f"Saved users in {output_file.name}")
        elif output_mode == "id":
            click.echo(','.join([user["id"] for user in users_list]))
        elif output_mode == "login":
            click.echo(','.join([user["profile"]["login"] for user in users_list]))
        elif output_mode == "json":
            click.echo(users_list)
        elif output_mode == "csv":
            tabulate(users_list, all=True, mode="csv")
        else:
            tabulate(users_list, all=all)
        click.echo()


@cli.command(short_help='Deactivate users')
@global_options
@click.option('--confirm', '-y', is_flag=True, help='Confirm operation.')
@click.option('--notify', is_flag=True, help='Send email notification. Use caution.')
@click.option('--field', default="id", help='Attribute to find users.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--prefix', is_flag=True, help='Enable prefix search.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--file', '-f', is_flag=True, help='Header based CSV file containing target users.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])  # noqa: E501
@click.option('--conditions', '-c', is_flag=True, help='Search based on conditions.', cls=MutuallyExclusiveOption, mutually_exclusive=["file", "field", "prefix"])  # noqa: E501
@click.option('--pattern', '-e', is_flag=True, help='Search based on pattern or substring. Expensive operation.', cls=DependentOption, dependent_on=["conditions"])  # noqa: E501
@click.argument('query')
@click.pass_context
@timer
def deactivate(ctx, query, confirm, notify, field, prefix, file, conditions, pattern, **kwargs):
    """Deactivates users."""

    success = []
    failure = []
    debug = kwargs["debug"]

    userMgr = get_handler(ctx, kwargs["profile"], "user")

    try:
        targets = _retrieve_target_ids(userMgr,
                                       query=query,
                                       operation="deactivate",
                                       field=field,
                                       prefix=prefix,
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
            click.echo("No target users(s) to deactivate.")
            sys.exit(0)

        if confirm or click.confirm(f"{len(targets)} user(s) are going to be deactivated. Proceed?"):
            result = userMgr.deactivateUsers(targets, notify=notify)
            success = result["success"]
            failure = result["failure"]
            datestr = datetime.now().strftime("%Y%m%d-%H%M%S")

            click.echo(f"{len(success)} user(s) successfully deactivated.")
            if len(success) > 0:
                successFile = "okt_user_deactivate_success_" + datestr + ".txt"
                with open(successFile, 'w') as outfile:
                    json.dump(success, outfile)
            if len(failure) > 0:
                click.echo(f"Deactivation failed for {len(failure)} user(s).")
                failureFile = "okt_user_deactivate_failed_" + datestr + ".txt"
                with open(failureFile, 'w') as outfile:
                    json.dump(failure, outfile)

            if debug:
                errors = result["errors"]
                if len(errors) > 0:
                    errorFile = "okt_errors_user_deactivate_" + datestr + ".log"
                    with open(errorFile, 'w') as outfile:
                        json.dump(errors, outfile)
                        click.echo(f"Error information saved to {errorFile}")
        else:
            click.echo("Cancelled.")

    click.echo()


@cli.command(short_help='Delete users')
@global_options
@click.option('--confirm', '-y', is_flag=True, help='Confirm operation.')
@click.option('--notify', is_flag=True, help='Send email notification. Use caution.')
@click.option('--field', default="id", help='Attribute to find users.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--prefix', is_flag=True, help='Enable prefix search.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])
@click.option('--file', '-f', is_flag=True, help='Header based CSV file containing target users.', cls=MutuallyExclusiveOption, mutually_exclusive=["conditions"])  # noqa: E501
@click.option('--conditions', '-c', is_flag=True, help='Search based on conditions.', cls=MutuallyExclusiveOption, mutually_exclusive=["file", "field", "prefix"])  # noqa: E501
@click.option('--pattern', '-e', is_flag=True, help='Search based on pattern or substring. Expensive operation.', cls=DependentOption, dependent_on=["conditions"])  # noqa: E501
@click.argument('query')
@click.pass_context
@timer
def delete(ctx, query, confirm, notify, field, prefix, file, conditions, pattern, **kwargs):
    """Delete users."""

    deactivate_success = []
    deactivate_failure = []
    success = []
    failure = []
    debug = kwargs["debug"]

    userMgr = get_handler(ctx, kwargs["profile"], "user")

    try:
        deactivate_targets = _retrieve_target_ids(userMgr,
                                                  query=query,
                                                  operation="deactivate",
                                                  field=field,
                                                  prefix=prefix,
                                                  file=file,
                                                  conditions=conditions,
                                                  pattern=pattern)
        delete_targets = _retrieve_target_ids(userMgr,
                                              query=query,
                                              operation="delete",
                                              field=field,
                                              prefix=prefix,
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
        targets = list(set(deactivate_targets + delete_targets))
        if len(targets) == 0:
            click.echo("No target users(s) to delete.")
            sys.exit(0)

        if confirm or click.confirm(f"{len(targets)} user(s) are going to be deleted. Proceed?"):
            result = None
            deactivate_result = userMgr.deactivateUsers(deactivate_targets)
            deactivate_success = deactivate_result["success"]
            deactivate_failure = deactivate_result["failure"]
            datestr = datetime.now().strftime("%Y%m%d-%H%M%S")

            final_targets = list(set(deactivate_success + delete_targets))
            if len(final_targets) > 0:
                result = userMgr.deleteUsers(final_targets, notify=notify)
                success = result["success"]
                failure = result["failure"]
                click.echo(f"{len(success)} user(s) successfully deleted.")
                if len(success) > 0:
                    successFile = "okt_user_delete_success_" + datestr + ".txt"
                    with open(successFile, 'w') as outfile:
                        json.dump(success, outfile)
                if len(failure) > 0:
                    click.echo(f"Deletion failed for {len(failure)} user(s).")
                    failureFile = "okt_user_delete_failed_" + datestr + ".txt"
                    with open(failureFile, 'w') as outfile:
                        json.dump(failure, outfile)

            if len(deactivate_failure) > 0:
                click.echo(f"Deactivation failed for {len(deactivate_failure)} user(s).")
                failureFile = "okt_user_delete_deactivation_failed_" + datestr + ".txt"
                with open(failureFile, 'w') as outfile:
                    json.dump(deactivate_failure, outfile)

            if debug:
                errors = []
                if deactivate_result:
                    errors = errors + deactivate_result["errors"]
                if result:
                    errors = errors + result["errors"]
                if len(errors) > 0:
                    errorFile = "okt_errors_user_delete_" + datestr + ".log"
                    with open(errorFile, 'w') as outfile:
                        json.dump(errors, outfile)
                        click.echo(f"Error information saved to {errorFile}")
        else:
            click.echo("Cancelled.")

    click.echo()


@cli.command(short_help='Create users')
@global_options
@click.option('--multiple', '-m', is_flag=True, help='Create multiple users', cls=MutuallyExclusiveOption, mutually_exclusive=["input_file"])
@click.option('--default-password', help='Default password for all users', cls=MutuallyExclusiveOption, mutually_exclusive=["no_password", "import_password", "input_file"])  # noqa: E501
@click.option('--no-password', is_flag=True, help='Create users without password', cls=MutuallyExclusiveOption, mutually_exclusive=["default_password", "import_password", "input_file"])  # noqa: E501
@click.option('--import-password', is_flag=True, help='Create password import hook enabled users', cls=MutuallyExclusiveOption, mutually_exclusive=["default_password", "no_password", "input_file"])  # noqa: E501
@click.option('--activate', is_flag=True, help='Create users without password')
@click.option('--file', '-f', 'input_file', help='Input file', cls=MutuallyExclusiveOption, mutually_exclusive=["default_password", "no_password", "import_password", "multiple"])
@click.option('--mode', default='json', help='User paylod format (JSON or CSV)', cls=DependentOption, dependent_on=["input_file"])
@click.option('--csv-options', help='Create user options', cls=DependentOption, dependent_on=["mode"])
@click.pass_context
@timer
def create(ctx, multiple, default_password, no_password, import_password, activate, input_file, mode, csv_options, **kwargs):
    """Create users."""

    debug = kwargs["debug"]

    user_payload = []

    if input_file is None:
        user_payload = _multiple_user_from_prompt(password=default_password,
                                                  password_import=import_password,
                                                  password_required=(not no_password) and (not import_password)) \
            if multiple \
            else _single_user_from_prompt(password=default_password,
                                          password_import=import_password,
                                          password_required=(not no_password) and (not import_password))

    options = {}
    if csv_options:
        patterns = csv_options.split(",")
        for p in patterns:
            components = p.split(":")
            if len(components) != 2:
                raise click.ClickException("Invalid options. Use `key1:value1[,key2:value2,...]` format.")
            key = components[0]
            val = components[1]
            if key in ["default-password", "hash-algorithm", "hash-salt-order"]:
                options[key] = val
            elif key in ["no-password", "import-password", "hashed-password", "hash-salt"]:
                options[key] = True if val.lower() == 'true' else False
    userMgr = get_handler(ctx, kwargs["profile"], "user")
    result = userMgr.createUsers(inputs=user_payload, file=input_file, mode=mode, options=options, activate=activate and (not import_password))

    success = result["success"]
    failure = result["failure"]
    datestr = datetime.now().strftime("%Y%m%d-%H%M%S")

    click.echo(f"{len(success)} user(s) successfully created.")

    if len(success) > 0:
        successFile = "okt_user_create_success_" + datestr + ".txt"
        with open(successFile, 'w') as outfile:
            json.dump(success, outfile)

    if len(failure) > 0:
        click.echo(f"Creation failed for {len(failure)} user(s).")

    if debug:
        errors = []
        if result:
            errors = errors + result["errors"]

            if len(failure) > 0:
                failureFile = "okt_user_create_failed_" + datestr + ".txt"
                with open(failureFile, 'w') as outfile:
                    json.dump(failure, outfile)

            if len(errors) > 0:
                errorFile = "okt_errors_user_create_" + datestr + ".log"
                with open(errorFile, 'w') as outfile:
                    json.dump(errors, outfile)
                    click.echo(f"Error information saved to {errorFile}")

    click.echo()
