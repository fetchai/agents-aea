from aea.test_tools.click_testing import CliRunner
from aea.cli.core import cli


def test_invoke():
    cli_runner = CliRunner()

    result = cli_runner.invoke(cli, ['--help'])
    assert "Command-line tool for setting up an Autonomous Economic Agent" in result.output

    result = cli_runner.invoke(cli, '--help')
    assert "Command-line tool for setting up an Autonomous Economic Agent" in result.output