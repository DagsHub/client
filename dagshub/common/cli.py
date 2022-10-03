import sys
import click

import dagshub.auth
from dagshub.common import config


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


@cli.command()
@click.option("--token", help="Login using a specified token")
@click.option("--host", help="DagsHub instance to which you want to login")
@click.pass_context
def login(ctx, **kwargs):
    host = kwargs["host"] or ctx.obj["host"]
    if kwargs["token"] is not None:
        dagshub.auth.add_app_token(kwargs["token"], host)
        print("Token added successfully")
    else:
        dagshub.auth.add_oauth_token(host)
        print("OAuth token added")


if __name__ == "__main__":
    cli()
