# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Implementation of the 'aea push' subcommand."""
import click

from aea.cli.registry.push import push_item


@click.group()
def push():
    """Push item to Registry."""
    pass


@push.command(name='connection')
@click.argument('connection-name', type=str, required=True)
def connection(connection_name):
    """Push connection to Registry."""
    push_item('connection', connection_name)


@push.command(name='protocol')
@click.argument('protocol-name', type=str, required=True)
def protocol(protocol_name):
    """Push protocol to Registry."""
    push_item('protocol', protocol_name)


@push.command(name='skill')
@click.argument('skill-name', type=str, required=True)
def skill(skill_name):
    """Push skill to Registry."""
    push_item('skill', skill_name)
