import click
import requests

from settings import API_URL


def request_api(method, path, params=None):
    resp = requests.request(
        method=method,
        url='{}{}'.format(API_URL, path),
        params=params
    )
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 403:
        raise click.ClickException('You are not authenticated.')
    else:
        raise click.ClickException(
            'Wrong server response. Status code: {}'.format(resp.status_code)
        )


def format_list(items):
    list_str = ''
    for item in items:
        list_str += (
            '{line}\n'
            'Name: {name}\n'
            'ID: {id}\n'
            'Description: {description}\n'
            '{line}\n'.format(
                name=item['name'],
                description=item['description'],
                id=item['id'],
                line='-'*30
        ))
    return list_str
