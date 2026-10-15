"""Vendor and checksum the genesis-idp Python package.

CI ``--check`` is offline: it hashes ``ring/vendor/genesis_idp`` against
the committed manifest. Recopying from neil/genesis needs a local clone
(``--from``); that path is not used in GitHub Actions.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parents[1] / "vendor"
PACKAGE_DIR = VENDOR_ROOT / "genesis_idp"
MANIFEST_PATH = VENDOR_ROOT / "genesis_idp.sha256"
VENDORED_FROM_NAME = "VENDORED_FROM"
DEFAULT_COMMIT = "bbdf2aa6c02ddb61d2a08fc1ac37fedbc31e0925"
DEFAULT_SOURCE_REPO = "https://origin.cursor.com/git/neil/genesis.git"
DEFAULT_SOURCE_PATH = "sdk/python/idp"
_SKIP_DIR_NAMES = {
    "__pycache__",
    "tests",
    "test",
    ".pytest_cache",
}
_SKIP_FILE_NAMES: set[str] = set()
_IMPORT_FROM_PKG = re.compile(
    r"^(\s*(?:from|import)\s+)genesis_idp((?:\.\w+)*\s+)",
    re.M,
)


class VendorGenesisIdpError(ValueError):
    """Vendored genesis-idp tree is missing, stale, or unverifiable."""


def _iter_package_files(package_dir: Path) -> list[Path]:
    files: list[Path] = []
    if not package_dir.is_dir():
        return files
    for path in package_dir.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(package_dir).parts
        if any(part in _SKIP_DIR_NAMES for part in rel_parts[:-1]):
            continue
        if path.name in _SKIP_FILE_NAMES or path.suffix == ".pyc":
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(package_dir).as_posix())


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_manifest(package_dir: Path = PACKAGE_DIR) -> str:
    """sha256sum-style lines for every file in the vendored package."""
    lines: list[str] = []
    for path in _iter_package_files(package_dir):
        rel = path.relative_to(package_dir).as_posix()
        lines.append(f"{_file_digest(path)}  {rel}")
    return "\n".join(lines) + ("\n" if lines else "")


def write_manifest(
    package_dir: Path = PACKAGE_DIR,
    manifest_path: Path = MANIFEST_PATH,
) -> Path:
    """Write the checksum manifest. Used after a recopy."""
    manifest_path.write_text(render_manifest(package_dir))
    return manifest_path


def parse_manifest(text: str) -> dict[str, str]:
    """Parse ``hash  relpath`` lines into a mapping."""
    entries: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        if not rel or len(digest) != 64:
            raise VendorGenesisIdpError(
                f"malformed genesis-idp manifest line: {raw!r}"
            )
        entries[rel] = digest
    return entries


def check_vendored_tree(
    package_dir: Path = PACKAGE_DIR,
    manifest_path: Path = MANIFEST_PATH,
) -> str:
    """Return a human diff if the tree was hand-edited; empty if current."""
    if not manifest_path.is_file():
        raise VendorGenesisIdpError(
            f"missing checksum manifest {manifest_path}"
        )
    if not package_dir.is_dir():
        raise VendorGenesisIdpError(f"missing vendored package {package_dir}")
    expected = parse_manifest(manifest_path.read_text())
    actual = {
        path.relative_to(package_dir).as_posix(): _file_digest(path)
        for path in _iter_package_files(package_dir)
    }
    problems: list[str] = []
    for rel in sorted(set(expected) | set(actual)):
        if rel not in expected:
            problems.append(f"untracked {rel}")
        elif rel not in actual:
            problems.append(f"missing {rel}")
        elif expected[rel] != actual[rel]:
            problems.append(f"modified {rel}")
    return "\n".join(problems)


def _find_genesis_package(genesis_root: Path) -> Path:
    candidates = [
        genesis_root / "sdk" / "python" / "idp" / "src" / "genesis_idp",
        genesis_root / "sdk" / "python" / "idp" / "genesis_idp",
        genesis_root / "src" / "genesis_idp",
        genesis_root / "genesis_idp",
    ]
    for path in candidates:
        if (path / "__init__.py").is_file():
            return path
    raise VendorGenesisIdpError(
        "could not find genesis_idp under "
        f"{genesis_root} (tried sdk/python/idp[/src]/genesis_idp)"
    )


def _rewrite_imports(text: str) -> str:
    return _IMPORT_FROM_PKG.sub(r"\1ring.vendor.genesis_idp\2", text)


def _resolve_commit(genesis_root: Path, commit: str | None) -> str:
    if commit:
        return commit
    try:
        result = subprocess.run(
            ["git", "-C", str(genesis_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return DEFAULT_COMMIT
    return result.stdout.strip() or DEFAULT_COMMIT


def write_vendored_from(
    package_dir: Path,
    *,
    commit: str,
    source_repo: str = DEFAULT_SOURCE_REPO,
    source_path: str = DEFAULT_SOURCE_PATH,
) -> Path:
    """Record where this snapshot was copied from."""
    path = package_dir / VENDORED_FROM_NAME
    path.write_text(
        "\n".join(
            [
                f"source_repo={source_repo}",
                f"source_path={source_path}",
                f"commit={commit}",
                "package=genesis_idp",
                "note=Refresh with `ring gen genesis-idp --from "
                "<genesis clone or extracted sdk/python/idp>`.",
                "",
            ]
        )
    )
    return path


def vendor_from_genesis(
    genesis_root: Path,
    *,
    commit: str | None = None,
    dest: Path = PACKAGE_DIR,
) -> Path:
    """Replace the vendored package from a local neil/genesis checkout.

    Does not clone Origin. ``genesis_root`` must already contain
    ``sdk/python/idp``.
    """
    source = _find_genesis_package(genesis_root)
    resolved = _resolve_commit(genesis_root, commit)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        if any(part in _SKIP_DIR_NAMES for part in rel.parts):
            continue
        if path.name in _SKIP_FILE_NAMES:
            continue
        target = dest / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".py":
            target.write_text(_rewrite_imports(path.read_text()))
        else:
            shutil.copy2(path, target)
    write_vendored_from(dest, commit=resolved)
    write_manifest(dest, MANIFEST_PATH)
    return dest
