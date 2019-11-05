import click

from search import search


@click.group()
def cli():
    pass


cli.add_command(search)


if __name__ == '__main__':
    cli()
