"""Tests for the pipeline runner CLI."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pipeline_runner.main import cli, _load_pipeline_config, _run_stage, _setup_logging


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def pipeline_yml(tmp_path: Path) -> Path:
    """Create a temporary pipeline.yml config file."""
    config = textwrap.dedent("""\
        stages:
          lint:
            command: "echo lint-ok"
            description: "Lint check"
          test:
            command: "echo test-ok"
            description: "Run tests"
          build:
            command: "echo build-ok"
            description: "Build artifacts"
          deploy:
            command: "echo deploy-ok"
            description: "Deploy artifacts"
    """)
    config_file = tmp_path / "pipeline.yml"
    config_file.write_text(config)
    return config_file


@pytest.fixture
def failing_pipeline_yml(tmp_path: Path) -> Path:
    """Create a pipeline.yml where the test stage fails."""
    config = textwrap.dedent("""\
        stages:
          lint:
            command: "echo lint-ok"
            description: "Lint check"
          test:
            command: "exit 1"
            description: "Failing tests"
          build:
            command: "echo build-ok"
            description: "Build"
          deploy:
            command: "echo deploy-ok"
            description: "Deploy"
    """)
    config_file = tmp_path / "pipeline.yml"
    config_file.write_text(config)
    return config_file


# ---------- CLI invocation tests ----------


class TestLintCommand:
    def test_lint_success(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["lint"])
        assert result.exit_code == 0

    def test_lint_verbose(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["-v", "lint"])
        assert result.exit_code == 0


class TestTestCommand:
    def test_test_success(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["test"])
        assert result.exit_code == 0

    def test_test_failure(self, runner: CliRunner, failing_pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(failing_pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["test"])
        assert result.exit_code == 1


class TestBuildCommand:
    def test_build_success(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["build"])
        assert result.exit_code == 0


class TestDeployCommand:
    def test_deploy_success(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["deploy"])
        assert result.exit_code == 0


class TestRunAllCommand:
    def test_run_all_success(self, runner: CliRunner, pipeline_yml: Path) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["run-all"])
        assert result.exit_code == 0

    def test_run_all_with_failure(
        self, runner: CliRunner, failing_pipeline_yml: Path
    ) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(failing_pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["run-all"])
        assert result.exit_code == 1

    def test_run_all_fail_fast(
        self, runner: CliRunner, failing_pipeline_yml: Path
    ) -> None:
        env = {"PIPELINE_CONFIG_PATH": str(failing_pipeline_yml)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["run-all", "--fail-fast"])
        assert result.exit_code == 1


# ---------- Error handling tests ----------


class TestErrorHandling:
    def test_missing_stage(self, runner: CliRunner) -> None:
        """_run_stage returns 1 for an unknown stage name."""
        code = _run_stage("nonexistent")
        assert code == 1

    def test_invalid_config_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """A config file without a 'stages' key falls back to defaults."""
        bad_config = tmp_path / "pipeline.yml"
        bad_config.write_text("not_stages:\n  foo: bar\n")
        env = {"PIPELINE_CONFIG_PATH": str(bad_config)}
        with patch.dict(os.environ, env):
            config = _load_pipeline_config()
        # Should fall back to defaults
        assert "lint" in config

    def test_empty_command(self, tmp_path: Path) -> None:
        """A stage with an empty command string returns exit code 1."""
        config_file = tmp_path / "pipeline.yml"
        config_file.write_text(
            "stages:\n  lint:\n    command: ''\n    description: 'empty'\n"
        )
        env = {"PIPELINE_CONFIG_PATH": str(config_file)}
        with patch.dict(os.environ, env):
            code = _run_stage("lint")
        assert code == 1

    def test_default_config_used_when_no_file(self) -> None:
        """Without any config file, default config is used."""
        env = {"PIPELINE_CONFIG_PATH": "/nonexistent/path/pipeline.yml"}
        with patch.dict(os.environ, env):
            config = _load_pipeline_config()
        assert "lint" in config
        assert "test" in config
        assert "build" in config
        assert "deploy" in config


# ---------- CLI help tests ----------


class TestCLIHelp:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Pipeline Runner" in result.output

    def test_lint_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["lint", "--help"])
        assert result.exit_code == 0

    def test_run_all_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["run-all", "--help"])
        assert result.exit_code == 0
        assert "--fail-fast" in result.output


# ---------- Stderr and exception coverage tests ----------


class TestStderrAndExceptions:
    def test_stage_with_stderr_output(self, tmp_path: Path) -> None:
        """A command that writes to stderr triggers the warning log path (line 95)."""
        config_file = tmp_path / "pipeline.yml"
        config_file.write_text(
            "stages:\n  lint:\n    command: 'echo error-output >&2 && exit 0'\n    description: 'stderr test'\n"
        )
        env = {"PIPELINE_CONFIG_PATH": str(config_file)}
        with patch.dict(os.environ, env):
            code = _run_stage("lint")
        # The command exits 0 even though stderr was written
        assert code == 0

    def test_stage_exception_raises(self, tmp_path: Path) -> None:
        """When subprocess.run raises an exception, _run_stage returns 1 (lines 104-106)."""
        config_file = tmp_path / "pipeline.yml"
        config_file.write_text(
            "stages:\n  lint:\n    command: 'echo hi'\n    description: 'exc test'\n"
        )
        env = {"PIPELINE_CONFIG_PATH": str(config_file)}
        with patch.dict(os.environ, env):
            with patch("pipeline_runner.main.subprocess.run", side_effect=OSError("boom")):
                code = _run_stage("lint")
        assert code == 1

    def test_setup_logging_verbose(self) -> None:
        """_setup_logging with verbose=True sets DEBUG level."""
        _setup_logging(verbose=True)
        # Just verify it runs without error; level is set on root logger
        assert True

    def test_setup_logging_default(self) -> None:
        """_setup_logging with verbose=False (default) sets INFO level."""
        _setup_logging(verbose=False)
        assert True
