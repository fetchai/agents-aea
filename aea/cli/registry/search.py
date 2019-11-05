import click

from utils import format_list, request_api


@click.group()
def search():
    """Search for protocols/skills/agents/connections."""
    pass


@search.command()
@click.option('--query', prompt='Protocol search query',
              help='Query string to search Protocols by name.')
def protocols(query):
    """Search for Protocols."""
    click.echo('Searching for "{}"...'.format(query))
    resp = request_api(
        'GET', '/protocols', params={'search': query}
    )
    if not len(resp):
        click.echo('No protocols found.')
    else:
        click.echo('Protocols found:\n')
        click.echo(format_list(resp))


@search.command()
@click.option('--query', prompt='Skill search query',
              help='Query string to search Skills by name.')
def skills(query):
    """Search for Skills."""
    click.echo('Searching for "{}"...'.format(query))
    resp = request_api(
        'GET', '/skills', params={'search': query}
    )
    if not len(resp):
        click.echo('No skills found.')
    else:
        click.echo('Protocols found:\n')
        click.echo(format_list(resp))
