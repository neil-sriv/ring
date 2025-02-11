from typing import Any

from dev_util.compose import compose_exec
from dev_util.dev import UNLIMITED_ARGS_SETTINGS, cmd_run, dev_group

GH_ECR_URI_BASE = "ghcr.io"


@dev_group("test")
def test() -> None:
    pass


@test.group("python", context_settings=UNLIMITED_ARGS_SETTINGS)
def python() -> None:
    pass


@cmd_run("image", test)
def image(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[list[str]]:
    image_tag = f"{GH_ECR_URI_BASE}/neil-sriv/ring/ring-test-runner:latest"
    return [
        [
            "docker",
            "tag",
            "ring-test-runner:latest",
            image_tag,
        ],
        [
            "docker",
            "push",
            image_tag,
        ],
    ]


@compose_exec(
    "run",
    python,
    service="test-runner",
    profile="test",
    cmd="run",
    opts=["--rm"],
)
def py_run(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "pytest",
        "-c",
        "ring/tests/pytest.ini",
    ]


@compose_exec(
    "server",
    python,
    service="test-runner",
    profile="test",
    cmd="run",
    opts=["--rm"],
)
def py_server(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "pytest",
        "-f",
        "-c",
        "ring/tests/pytest.ini",
        "--color=yes",
        "--code-highlight=yes",
    ]


@test.group("fe", context_settings=UNLIMITED_ARGS_SETTINGS)
def fe() -> None:
    pass


@compose_exec(
    "run",
    fe,
    service="fe-test-runner",
    profile="test",
    cmd="run",
    opts=["--rm"],
)
def fe_run(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "pytest",
        "-c",
        "ring/tests/pytest.ini",
    ]
