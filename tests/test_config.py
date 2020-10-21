from click.testing import CliRunner
from atkocli import cli


def test_cli_config():
    runner = CliRunner()
    result = runner.invoke(cli, ['config'])
    assert result.exit_code == 0
    assert ("Enter Okta Org" in result.output)


def test_cli_config_show():
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'show'])
    assert result.exit_code == 0
    assert ("Enter profile name" in result.output)
