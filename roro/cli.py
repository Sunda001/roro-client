import os
import stat
import click
import datetime
from netrc import netrc
from tabulate import tabulate
from . import projects
from . import helpers as h
from .projects import login as roro_login

from firefly.client import FireflyError
from requests import ConnectionError

@click.group()
def cli():
    pass

@cli.command()
@click.option('--email', prompt='Email address')
@click.option('--password', prompt=True, hide_input=True)
def login(email, password):
    """Login to rorodata platform.
    """
    netrc_file = create_netrc_if_not_exists()
    try:
        token = roro_login(email, password)
        rc = netrc()
        _fix_netrc(rc)
        with open(netrc_file, 'w') as f:
            rc.hosts[projects.SERVER_URL] = (email, None, token)
            f.write(str(rc))
    except ConnectionError:
        click.echo('unable to connect to the server, try again later')
    except FireflyError as e:
        click.echo(e)

# this is here because of this issue
# https://github.com/python/cpython/pull/2491
# TODO: should be removed once it is fixed
def _fix_netrc(rc):
    for host in rc.hosts:
        login, _, password = rc.hosts[host]
        # should be safe as we use alphanumneric chars in token
        login = login.strip("'")
        password = password.strip("'")
        rc.hosts[host] = (login, _, password)

def create_netrc_if_not_exists():
    prefix = '.' if os.name != 'nt' else '_'
    netrc_file = os.path.join(os.path.expanduser('~'), prefix+'netrc')
    # theese flags works both on windows and linux according to this stackoverflow
    # https://stackoverflow.com/questions/27500067/chmod-issue-to-change-file-permission-using-python#27500153
    if not os.path.exists(netrc_file):
        with open(netrc_file, 'w'):
            pass
        os.chmod(netrc_file, stat.S_IREAD|stat.S_IWRITE)
    return netrc_file

@cli.command()
@click.argument('project')
def create(project):
    """Creates a new Project.
    """
    pass

@cli.command()
def deploy():
    """Pushes the local changes to the cloud and restarts all the services.
    """
    pass

@cli.command()
def ps():
    """Shows all the processes running in this project.
    """
    project = projects.current_project()
    jobs = project.ps()
    rows = []
    for job in jobs:
        start = h.parse_time(job['start_time'])
        end = h.parse_time(job['end_time'])
        total_time = (end - start)
        total_time = datetime.timedelta(total_time.days, total_time.seconds)
        command = " ".join(job["details"]["command"])
        rows.append([job['jobid'], job['status'], h.datestr(start), str(total_time), job['instance_type'], h.truncate(command, 50)])
    print(tabulate(rows, headers=['JOBID', 'STATUS', 'WHEN', 'TIME', 'INSTANCE TYPE', 'CMD']))

@cli.command(name='ps:restart')
@click.argument('name')
def ps_restart(name):
    """Restarts the service specified by name.
    """
    pass

@cli.command()
def env():
    """Lists all environment variables associated with this project.
    """
    pass

@cli.command(name='env:set')
@click.argument('name')
@click.argument('value')
def env_set(name, value):
    """Lists all environment variables associated with this project.
    """
    pass

@cli.command(name='env:unset')
@click.argument('name')
@click.argument('value')
def env_unset(name, value):
    """Unsets an environment variable.
    """
    pass

@cli.command(context_settings={"allow_interspersed_args": False})
@click.argument('command', nargs=-1)
def run(command):
    """Runs the given script in foreground.
    """
    project = projects.current_project()
    job = project.run(command)
    print("Started new job", job["jobid"])

@cli.command(name='run:notebook')
def run_notebook():
    """Runs a notebook.
    """
    pass

@cli.command()
@click.argument('jobid')
def logs(jobid):
    """Shows all the logs of the project.
    """
    project = projects.current_project()
    logs = project.logs(jobid)
    for line in logs:
        print(line)

@cli.command()
@click.argument('project')
def project_logs(project):
    """Shows all the logs of the process with name <project> the project.
    """
    pass

@cli.command()
def volumes():
    """Lists all the volumes.
    """
    pass

@cli.command(name='volumes:new')
@click.argument('volume_name')
def create_volume(volume_name):
    """Creates a new volume.
    """
    pass

@cli.command(name='volumes:remove')
@click.argument('volume_name')
def remove_volume(volume_name):
    """Removes a new volume.
    """
    pass

def main_dev():
    projects.SERVER_URL = "http://api.local.rorodata.com:8080/"
    cli()