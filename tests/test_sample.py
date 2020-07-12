from click.testing import CliRunner
from okt import cli


def test_cli_config():
    runner = CliRunner()
    result = runner.invoke(cli, ['config'])
    assert result.exit_code == 0
    assert ("Enter Okta Org" in result.output)


def test_cli_config_list():
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'list'])
    assert result.exit_code == 0
    assert ("base_url" in result.output) and ("api_token" in result.output)
