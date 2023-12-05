import click
import json as pyjson

from itertools import chain
from typing import Optional

from toot import api
from toot.cli.validators import validate_instance
from toot.entities import Instance, Status, from_dict, Account
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_account, print_instance, print_search_results, print_status, print_timeline
from toot.cli.base import cli, json_option, pass_context, Context


@cli.command()
@json_option
@pass_context
def whoami(ctx: Context, json: bool):
    """Display logged in user details"""
    response = api.verify_credentials(ctx.app, ctx.user)

    if json:
        click.echo(response.text)
    else:
        account = from_dict(Account, response.json())
        print_account(account)


@cli.command()
@click.argument("account")
@json_option
@pass_context
def whois(ctx: Context, account: str, json: bool):
    """Display account details"""
    account_dict = api.find_account(ctx.app, ctx.user, account)

    # Here it's not possible to avoid parsing json since it's needed to find the account.
    if json:
        click.echo(pyjson.dumps(account_dict))
    else:
        account_obj = from_dict(Account, account_dict)
        print_account(account_obj)


@cli.command()
@click.argument("instance_url", required=False, callback=validate_instance)
@json_option
@pass_context
def instance(ctx: Context, instance_url: Optional[str], json: bool):
    """Display instance details"""
    default_url = ctx.app.base_url if ctx.app else None
    base_url = instance_url or default_url

    if not base_url:
        raise ConsoleError("Please specify an instance.")

    try:
        response = api.get_instance(base_url)
    except ApiError:
        raise ConsoleError(
            f"Instance not found at {base_url}.\n" +
            "The given domain probably does not host a Mastodon instance."
        )

    if json:
        print(response.text)
    else:
        instance = from_dict(Instance, response.json())
        print_instance(instance)


@cli.command()
@click.argument("query")
@click.option("-r", "--resolve", is_flag=True, help="Resolve non-local accounts")
@json_option
@pass_context
def search(ctx: Context, query: str, resolve: bool, json: bool):
    """Search for users or hashtags"""
    response = api.search(ctx.app, ctx.user, query, resolve)
    if json:
        print(response.text)
    else:
        print_search_results(response.json())


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def status(ctx: Context, status_id: str, json: bool):
    """Show a single status"""
    response = api.fetch_status(ctx.app, ctx.user, status_id)
    if json:
        print(response.text)
    else:
        status = from_dict(Status, response.json())
        print_status(status)


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def thread(ctx: Context, status_id: str, json: bool):
    """Show thread for a toot."""
    context_response = api.context(ctx.app, ctx.user, status_id)
    if json:
        print(context_response.text)
    else:
        toot = api.fetch_status(ctx.app, ctx.user, status_id).json()
        context = context_response.json()

        statuses = chain(context["ancestors"], [toot], context["descendants"])
        print_timeline(from_dict(Status, s) for s in statuses)
