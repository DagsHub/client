import argparse
import sys

import click

import dagshub.auth
from dagshub.common import config

parser = argparse.ArgumentParser(prog="dagshub")


@click.group()
@click.option("--host", default=config.host, help="Hostname of DagsHub instance")
@click.pass_context
def cli(ctx, host):
    ctx.obj = {"host": host.strip("/")}


@cli.command()
@click.argument("project_root", default=".")
@click.option("--repo_url", help="URL of the repo hosted on DagsHub")
@click.option("--branch", help="Repository's branch")
@click.option("--username", help="User's username")
@click.option("--password", help="User's password")
@click.option(
    "--debug", default=False, type=bool, help="URL of the repo hosted on DagsHub"
)
@click.pass_context
def mount(ctx, **kwargs):
    """
    Mount a DagsHub Storage folder via FUSE
    """
    # Since pyfuse can crash on init-time, import it here instead of up top
    from dagshub.streaming import mount

    if not kwargs["debug"]:
        # Hide tracebacks of errors, display only error message
        sys.tracebacklimit = 0
    mount(**kwargs)


@cli.group()
@click.pass_context
def auth(ctx):
    """
    Authentication commands
    """
    pass


@auth.command(name="add")
@click.argument("token")
@click.pass_context
def auth_add(ctx, token):
    """
    Add a long-lived auth token
    """
    dagshub.auth.add_app_token(token, ctx.obj["host"])
    print("Token added")


@auth.command(name="login")
@click.pass_context
def auth_login(ctx):
    """
    Add a short-lived OAuth token by logging in at DagsHub
    """
    dagshub.auth.add_oauth_token(ctx.obj["host"])
    print("Successfully stored OAuth token in cache")


if __name__ == "__main__":
    cli()
