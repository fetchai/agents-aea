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

"""Test the CLI plugin mechanism."""
import inspect
from pathlib import Path

import click
import pytest
from pkg_resources import Distribution, EntryPoint, iter_entry_points, working_set

# Create a few CLI commands for testing
from aea.cli.plugin import with_plugins
from aea.test_tools.click_testing import CliRunner

from tests.conftest import ROOT_DIR


# We need to compute the right dotted path w.r.t. the current module location.
# Instead of hard-coding it, we compute it on-the-fly.
_PATH_TO_THIS_MODULE = (
    Path(inspect.getfile(inspect.currentframe()))  # type: ignore
    .absolute()
    .relative_to(Path(ROOT_DIR).resolve())
)
_DOTTED_PATH = ".".join(_PATH_TO_THIS_MODULE.with_suffix("").parts)


@pytest.fixture(scope="function")
def runner(request):
    """Get a click.CliRunner instance."""
    return CliRunner()


@click.command()
@click.argument("arg")
def cmd1(arg):
    """Test command 1"""
    click.echo("passed")


@click.command()
@click.argument("arg")
def cmd2(arg):
    """Test command 2"""
    click.echo("passed")


class DistStub(Distribution):
    """
    Manually register plugins in an entry point and put broken plugins in a different entry point.

    The `DistStub()` class gets around an exception that is raised when
    `entry_point.load()` is called.  By default `load()` has `requires=True`
    which calls `dist.requires()` and the `click.group()` decorator
    doesn't allow us to change this.  Because we are manually registering these
    plugins the `dist` attribute is `None` so we can just create a stub that
    always returns an empty list since we don't have any requirements.  A full
    `pkg_resources.Distribution()` instance is not needed because there isn't
    a package installed anywhere.
    """

    def requires(self, *args):
        """Implement a dummy 'requires' function."""
        return []


working_set.by_key["click"]._ep_map = {  # type: ignore
    "_test_click_plugins.test_plugins": {
        "cmd1": EntryPoint.parse(f"cmd1={_DOTTED_PATH}:cmd1", dist=DistStub()),
        "cmd2": EntryPoint.parse(f"cmd2={_DOTTED_PATH}:cmd2", dist=DistStub()),
    },
    "_test_click_plugins.broken_plugins": {
        "before": EntryPoint.parse(
            "before=tests.broken_plugins:before", dist=DistStub()
        ),
        "after": EntryPoint.parse("after=tests.broken_plugins:after", dist=DistStub()),
        "do_not_exist": EntryPoint.parse(
            "do_not_exist=tests.broken_plugins:do_not_exist", dist=DistStub()
        ),
    },
}


# Main CLI groups - one with good plugins attached and the other broken
@with_plugins(iter_entry_points("_test_click_plugins.test_plugins"))
@click.group()
def good_cli():
    """Good CLI group."""
    pass


@with_plugins(iter_entry_points("_test_click_plugins.broken_plugins"))
@click.group()
def broken_cli():
    """Broken CLI group."""
    pass


def test_registered():
    """
    Make sure the plugins are properly registered.

    If this test fails it means that some of the for loops in other tests may not be executing.
    """
    assert len([ep for ep in iter_entry_points("_test_click_plugins.test_plugins")]) > 1
    assert (
        len([ep for ep in iter_entry_points("_test_click_plugins.broken_plugins")]) > 1
    )


def test_register_and_run(runner):
    """Test that registration and run of the command work correctly."""

    result = runner.invoke(good_cli)
    assert result.exit_code == 0

    for ep in iter_entry_points("_test_click_plugins.test_plugins"):
        cmd_result = runner.invoke(good_cli, [ep.name, "something"])
        assert cmd_result.exit_code == 0
        assert cmd_result.output.strip() == "passed"


def test_broken_register_and_run(runner):
    """Test that the broken plugin doesn't get registered as expected."""
    result = runner.invoke(broken_cli)
    assert result.exit_code == 0

    for ep in iter_entry_points("_test_click_plugins.broken_plugins"):
        cmd_result = runner.invoke(broken_cli, [ep.name])
        assert cmd_result.exit_code != 0
        assert "Traceback" in cmd_result.output


def test_group_chain(runner):
    """Test the plugin with nested CLI command group levels."""

    # Attach a sub-group to a CLI and get execute it without arguments to make
    # sure both the sub-group and all the parent group's commands are present
    @good_cli.group()
    def sub_cli():
        """Sub CLI."""
        pass

    result = runner.invoke(good_cli)
    assert result.exit_code == 0
    assert sub_cli.name in result.output
    for ep in iter_entry_points("_test_click_plugins.test_plugins"):
        assert ep.name in result.output

    # Same as above but the sub-group has plugins
    @with_plugins(plugins=iter_entry_points("_test_click_plugins.test_plugins"))
    @good_cli.group(name="sub-cli-plugins")
    def sub_cli_plugins():
        """Sub CLI with plugins."""
        pass

    result = runner.invoke(good_cli, ["sub-cli-plugins"])
    assert result.exit_code == 0
    for ep in iter_entry_points("_test_click_plugins.test_plugins"):
        assert ep.name in result.output

    print(result.output)

    # Execute one of the sub-group's commands
    result = runner.invoke(good_cli, ["sub-cli-plugins", "cmd1", "something"])
    assert result.exit_code == 0
    assert result.output.strip() == "passed"


def test_exception():
    """Test the 'with_plugins' decorator when it gets used on a non-click.Group object."""

    # Decorating something that isn't a click.Group() should fail
    with pytest.raises(TypeError):

        @with_plugins([])
        @click.command()
        def cli():
            """Whatever"""


def test_broken_register_and_run_with_help(runner):
    """Test the broken registration of the plugin when the command is run with the '--help' flag."""
    result = runner.invoke(broken_cli)
    assert result.exit_code == 0

    for ep in iter_entry_points("_test_click_plugins.broken_plugins"):
        cmd_result = runner.invoke(broken_cli, [ep.name, "--help"])
        assert cmd_result.exit_code != 0
        assert "Traceback" in cmd_result.output


def test_broken_register_and_run_with_args(runner):
    """Test the broken registration of the plugin when the command is run with the '--help' flag."""
    result = runner.invoke(broken_cli)
    assert result.exit_code == 0

    for ep in iter_entry_points("_test_click_plugins.broken_plugins"):
        cmd_result = runner.invoke(broken_cli, [ep.name, "-a", "b"])
        assert cmd_result.exit_code != 0
        assert "Traceback" in cmd_result.output
