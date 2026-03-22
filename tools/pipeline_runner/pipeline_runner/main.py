"""CLI entry point for the pipeline runner."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import yaml

logger = logging.getLogger("pipeline_runner")

DEFAULT_PIPELINE_CONFIG: dict[str, dict[str, Any]] = {
    "lint": {"command": "echo 'Running linter...'", "description": "Run linting checks"},
    "test": {"command": "echo 'Running tests...'", "description": "Run test suite"},
    "build": {"command": "echo 'Running build...'", "description": "Build the project"},
    "deploy": {"command": "echo 'Running deploy...'", "description": "Deploy the project"},
}


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging for the pipeline runner."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _load_pipeline_config() -> dict[str, dict[str, Any]]:
    """Load pipeline configuration from pipeline.yml or environment.

    Checks, in order:
      1. PIPELINE_CONFIG_PATH environment variable
      2. pipeline.yml in the current directory

    Falls back to DEFAULT_PIPELINE_CONFIG if no config file is found.
    """
    config_path_env = os.environ.get("PIPELINE_CONFIG_PATH")
    if config_path_env:
        config_path = Path(config_path_env)
    else:
        config_path = Path("pipeline.yml")

    if config_path.is_file():
        logger.debug("Loading pipeline config from %s", config_path)
        with open(config_path, "r") as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict) and "stages" in data:
            return data["stages"]  # type: ignore[no-any-return]
        logger.warning("Config file found but missing 'stages' key; using defaults")

    logger.debug("Using default pipeline configuration")
    return DEFAULT_PIPELINE_CONFIG


def _run_stage(stage_name: str) -> int:
    """Execute a single pipeline stage and return the exit code.

    Returns 0 on success, 1 on failure.
    """
    config = _load_pipeline_config()
    stage = config.get(stage_name)

    if stage is None:
        logger.error("Stage '%s' not found in pipeline configuration", stage_name)
        return 1

    command: str = stage.get("command", "")
    description: str = stage.get("description", stage_name)

    if not command:
        logger.error("No command defined for stage '%s'", stage_name)
        return 1

    logger.info("=== Stage: %s ===", stage_name)
    logger.info("Description: %s", description)
    logger.info("Command: %s", command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            logger.info("stdout:\n%s", result.stdout.rstrip())
        if result.stderr:
            logger.warning("stderr:\n%s", result.stderr.rstrip())

        if result.returncode == 0:
            logger.info("Stage '%s' completed successfully", stage_name)
        else:
            logger.error(
                "Stage '%s' failed with exit code %d", stage_name, result.returncode
            )
        return result.returncode
    except Exception as exc:
        logger.error("Stage '%s' raised an exception: %s", stage_name, exc)
        return 1


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """Pipeline Runner - execute CI/CD pipeline stages."""
    _setup_logging(verbose=verbose)


@cli.command()
def lint() -> None:
    """Run the lint stage."""
    code = _run_stage("lint")
    sys.exit(code)


@cli.command()
def test() -> None:
    """Run the test stage."""
    code = _run_stage("test")
    sys.exit(code)


@cli.command()
def build() -> None:
    """Run the build stage."""
    code = _run_stage("build")
    sys.exit(code)


@cli.command()
def deploy() -> None:
    """Run the deploy stage."""
    code = _run_stage("deploy")
    sys.exit(code)


@cli.command("run-all")
@click.option(
    "--fail-fast",
    is_flag=True,
    default=False,
    help="Stop on first stage failure",
)
def run_all(fail_fast: bool) -> None:
    """Run all pipeline stages in order: lint, test, build, deploy."""
    stages = ["lint", "test", "build", "deploy"]
    failed: list[str] = []

    for stage_name in stages:
        code = _run_stage(stage_name)
        if code != 0:
            failed.append(stage_name)
            if fail_fast:
                logger.error("Stopping early due to --fail-fast")
                break

    if failed:
        logger.error("Pipeline finished with failures in: %s", ", ".join(failed))
        sys.exit(1)
    else:
        logger.info("All pipeline stages completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    cli()
