"""AST generator for decorator-registry import factories.

SQLAlchemy ``Base.metadata`` and the decorator registries
(``JOB_REGISTRY``, ``INTERVAL_JOB_SCHEDULE_REGISTRY``,
``SEARCH_REGISTRY``, ``API_CLASS_REGISTRY``, ``ALL_FACTORIES``) only
fill when the defining modules are imported. This module walks the
tree with the AST — it does not import application code — and writes
the ``_gen`` import factories.

Regenerate with ``ring gen imports``. ``--check`` is the CI freshness
gate.
"""

from __future__ import annotations

import ast
import difflib
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RING_DIR = REPO_ROOT / "ring"
FACTORIES_DIR = RING_DIR / "tests" / "factories"

SQLA_BASE_MODULE = "ring.sqlalchemy_base"
SQLA_BASE_NAME = "Base"
SQLA_TABLE_MODULES = {"sqlalchemy", "sqlalchemy.schema"}

JOB_DECORATORS = frozenset({"job_factory", "interval_job_factory"})
SEARCH_DECORATOR = "register_search_function"
API_DECORATOR = "register_api_class"
FACTORY_DECORATOR = "register_factory"

SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".venv",
        "alembic",
        "packages",
        "_gen",
        "tests",
    }
)

GENERATED_HEADER = (
    "# GENERATED - do not edit. Regenerate with `ring gen imports`.\n"
)

MODELS_PATH = RING_DIR / "fastapp" / "_gen" / "all_sqla_models.py"
JOBS_PATH = RING_DIR / "fastapp" / "_gen" / "all_jobs.py"
SEARCH_PATH = RING_DIR / "search" / "_gen" / "all_search_registration.py"
FACTORIES_PATH = FACTORIES_DIR / "entrypoint" / "hydrate_registries.py"


class ImportFactoryError(ValueError):
    """Generated import factories are missing or inconsistent."""


@dataclass(frozen=True, order=True)
class ImportedName:
    module: str
    name: str


def py_module(path: Path, repo_root: Path = REPO_ROOT) -> str:
    """Dotted module path for a ``.py`` file under ``repo_root``."""
    rel = path.relative_to(repo_root)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def iter_py_files(root: Path, skip_dir_names: frozenset[str]) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = sorted(
            name for name in dirnames if name not in skip_dir_names
        )
        for name in sorted(filenames):
            if name.endswith(".py"):
                files.append(dirpath / name)
    return files


def _dotted(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        left = _dotted(expr.value)
        if left is None:
            return None
        return f"{left}.{expr.attr}"
    return None


def _parse_imports(tree: ast.Module, current_module: str) -> dict[str, str]:
    """Map local names to ``module.Name`` or a module path."""
    resolved: dict[str, str] = {}
    package = current_module.rsplit(".", 1)[0] if "." in current_module else ""
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                resolved[local] = alias.name
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            module = node.module or ""
        elif node.level == 1:
            module = (
                f"{package}.{node.module}"
                if node.module and package
                else (node.module or package)
            )
        else:
            parts = current_module.split(".")
            prefix = parts[: -node.level]
            module = ".".join(
                [*prefix, node.module] if node.module else prefix
            )
        for alias in node.names:
            local = alias.asname or alias.name
            if alias.name == "*":
                continue
            resolved[local] = (
                f"{module}.{alias.name}" if module else alias.name
            )
    return resolved


def _resolve_name(
    name: str, imports: dict[str, str], current_module: str
) -> str:
    if name in imports:
        return imports[name]
    if "." in name:
        first, rest = name.split(".", 1)
        if first in imports:
            imported = imports[first]
            return f"{imported}.{rest}"
    return f"{current_module}.{name}"


def _decorator_qualname(
    decorator: ast.expr, imports: dict[str, str], current_module: str
) -> str:
    expr = decorator.func if isinstance(decorator, ast.Call) else decorator
    dotted = _dotted(expr)
    if dotted is None:
        return ""
    return _resolve_name(dotted, imports, current_module)


def _decorator_basename(qualname: str) -> str:
    return qualname.rsplit(".", 1)[-1]


def _first_const_str(call: ast.Call) -> str | None:
    if not call.args:
        return None
    arg0 = call.args[0]
    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
        return arg0.value
    return None


def _is_module_level_table(
    node: ast.Assign | ast.AnnAssign,
    imports: dict[str, str],
) -> str | None:
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    dotted = _dotted(value.func)
    if dotted is None:
        return None
    if dotted == "Table":
        target = imports.get("Table", "")
        if not target.startswith("sqlalchemy"):
            return None
    elif dotted.endswith(".Table"):
        first = dotted.split(".", 1)[0]
        imported = imports.get(first, first)
        if imported not in SQLA_TABLE_MODULES and not imported.startswith(
            "sqlalchemy"
        ):
            return None
    else:
        return None
    targets: list[ast.expr]
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif node.target is not None:
        targets = [node.target]
    else:
        return None
    if len(targets) != 1 or not isinstance(targets[0], ast.Name):
        return None
    return targets[0].id


@dataclass
class _ModuleInfo:
    module: str
    classes: dict[str, list[str]]
    tables: list[str]
    job_modules: bool
    job_names: list[str]
    search_functions: list[str]
    api_classes: list[str]
    factories: list[str]


def _load_module(path: Path, repo_root: Path) -> _ModuleInfo:
    source = path.read_text()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise ImportFactoryError(f"{path}: {exc}") from exc
    module = py_module(path, repo_root)
    imports = _parse_imports(tree, module)
    classes: dict[str, list[str]] = {}
    tables: list[str] = []
    job_names: list[str] = []
    search_functions: list[str] = []
    api_classes: list[str] = []
    factories: list[str] = []
    has_job = False
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            table_name = _is_module_level_table(node, imports)
            if table_name is not None:
                tables.append(table_name)
            continue
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                dotted = _dotted(base)
                if dotted is not None:
                    bases.append(_resolve_name(dotted, imports, module))
            classes[f"{module}.{node.name}"] = bases
            for decorator in node.decorator_list:
                basename = _decorator_basename(
                    _decorator_qualname(decorator, imports, module)
                )
                if basename == API_DECORATOR:
                    api_classes.append(node.name)
                elif basename == FACTORY_DECORATOR:
                    factories.append(node.name)
            continue
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            basename = _decorator_basename(
                _decorator_qualname(decorator, imports, module)
            )
            if basename in JOB_DECORATORS:
                has_job = True
                if isinstance(decorator, ast.Call):
                    job_name = _first_const_str(decorator)
                    if job_name:
                        job_names.append(job_name)
            elif basename == SEARCH_DECORATOR:
                search_functions.append(node.name)
    return _ModuleInfo(
        module=module,
        classes=classes,
        tables=tables,
        job_modules=has_job,
        job_names=job_names,
        search_functions=search_functions,
        api_classes=api_classes,
        factories=factories,
    )


def _ring_modules(ring_dir: Path, repo_root: Path) -> list[_ModuleInfo]:
    return [
        _load_module(path, repo_root)
        for path in iter_py_files(ring_dir, SKIP_DIR_NAMES)
    ]


def _sqla_models(modules: list[_ModuleInfo]) -> list[ImportedName]:
    bases: dict[str, list[str]] = {}
    for info in modules:
        bases.update(info.classes)
    root = f"{SQLA_BASE_MODULE}.{SQLA_BASE_NAME}"
    models: set[str] = set()
    changed = True
    while changed:
        changed = False
        for qualname, class_bases in bases.items():
            if qualname in models:
                continue
            if root in class_bases or any(
                base in models for base in class_bases
            ):
                models.add(qualname)
                changed = True
    names = [
        ImportedName(
            module=qualname.rsplit(".", 1)[0], name=qualname.rsplit(".", 1)[1]
        )
        for qualname in models
        if qualname != root
    ]
    names.extend(
        ImportedName(module=info.module, name=table)
        for info in modules
        for table in info.tables
    )
    return sorted(set(names))


def discover_sqla_symbols(
    ring_dir: Path = RING_DIR, repo_root: Path = REPO_ROOT
) -> list[ImportedName]:
    symbols = _sqla_models(_ring_modules(ring_dir, repo_root))
    if not symbols:
        raise ImportFactoryError("discovered no SQLAlchemy models or tables")
    return symbols


def discover_job_modules(
    ring_dir: Path = RING_DIR, repo_root: Path = REPO_ROOT
) -> list[str]:
    modules = sorted(
        info.module
        for info in _ring_modules(ring_dir, repo_root)
        if info.job_modules
    )
    if not modules:
        raise ImportFactoryError("discovered no job modules")
    return modules


def discover_job_names(
    ring_dir: Path = RING_DIR, repo_root: Path = REPO_ROOT
) -> list[str]:
    return sorted(
        {
            name
            for info in _ring_modules(ring_dir, repo_root)
            for name in info.job_names
        }
    )


def discover_search_functions(
    ring_dir: Path = RING_DIR, repo_root: Path = REPO_ROOT
) -> list[ImportedName]:
    symbols = [
        ImportedName(module=info.module, name=func)
        for info in _ring_modules(ring_dir, repo_root)
        for func in info.search_functions
    ]
    if not symbols:
        raise ImportFactoryError("discovered no search registrations")
    return sorted(symbols)


def discover_api_classes(
    ring_dir: Path = RING_DIR, repo_root: Path = REPO_ROOT
) -> list[ImportedName]:
    return sorted(
        ImportedName(module=info.module, name=cls)
        for info in _ring_modules(ring_dir, repo_root)
        for cls in info.api_classes
    )


def discover_factories(
    factories_dir: Path = FACTORIES_DIR, repo_root: Path = REPO_ROOT
) -> list[ImportedName]:
    skip = frozenset({"__pycache__", "entrypoint"})
    symbols = [
        ImportedName(module=info.module, name=cls)
        for info in (
            _load_module(path, repo_root)
            for path in iter_py_files(factories_dir, skip)
        )
        for cls in info.factories
    ]
    if not symbols:
        raise ImportFactoryError("discovered no test factories")
    return sorted(symbols)


def verify_api_classes_are_models(
    models: list[ImportedName],
    api_classes: list[ImportedName],
) -> None:
    model_set = set(models)
    missing = [cls for cls in api_classes if cls not in model_set]
    if missing:
        listed = ", ".join(f"{item.module}.{item.name}" for item in missing)
        raise ImportFactoryError(
            f"@register_api_class classes are not Base subclasses: {listed}"
        )


def _grouped(names: list[ImportedName]) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in names:
        grouped[item.module].append(item.name)
    return [
        (module, sorted(set(group)))
        for module, group in sorted(grouped.items())
    ]


def _render_from_import(module: str, names: list[str], indent: str) -> str:
    single = f"{indent}from {module} import {', '.join(names)}"
    if len(single) <= 79:
        return single
    inner = ",\n".join(f"{indent}    {name}" for name in names)
    return f"{indent}from {module} import (\n{inner},\n{indent})"


def _render_from_imports(
    names: list[ImportedName], indent: str = "    "
) -> str:
    return "\n".join(
        _render_from_import(module, group, indent)
        for module, group in _grouped(names)
    )


def _ruff_stdin(args: list[str], source: str, path: Path) -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            *args,
            "--stdin-filename",
            str(path),
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ImportFactoryError(
            f"ruff {' '.join(args)} failed for {path}:\n"
            f"{result.stderr or result.stdout}"
        )
    return result.stdout


def format_generated(source: str, path: Path) -> str:
    formatted = _ruff_stdin(["format"], source, path)
    return _ruff_stdin(["check", "--fix", "--select", "I"], formatted, path)


def render_models(names: list[ImportedName]) -> str:
    body = _render_from_imports(names)
    return (
        f"{GENERATED_HEADER}\n"
        "from __future__ import annotations\n\n\n"
        "def import_all_sqla_models() -> None:\n"
        '    """Import all SQLAlchemy models."""\n'
        f"{body}\n"
    )


def render_jobs(modules: list[str]) -> str:
    imports = "\n".join(f"    import {module}" for module in modules)
    return (
        f"{GENERATED_HEADER}\n"
        "from __future__ import annotations\n\n\n"
        "def import_all_jobs() -> None:\n"
        '    """Import all jobs."""\n'
        f"{imports}\n\n\n"
        "def initialize() -> None:\n"
        "    import_all_jobs()\n"
    )


def render_search(names: list[ImportedName]) -> str:
    body = _render_from_imports(names)
    return (
        f"{GENERATED_HEADER}\n"
        "from __future__ import annotations\n\n\n"
        "def import_all_search_registrations() -> None:\n"
        '    """Import all search registrations."""\n'
        f"{body}\n"
    )


def render_factories(names: list[ImportedName]) -> str:
    body = _render_from_imports(names)
    return (
        f"{GENERATED_HEADER}\n"
        "from __future__ import annotations\n\n\n"
        "def hydrate_factories_registry():\n"
        f"{body}\n\n\n"
        "def hydrate_all_registries():\n"
        "    hydrate_factories_registry()\n"
    )


def generated_files(
    ring_dir: Path = RING_DIR,
    factories_dir: Path = FACTORIES_DIR,
    repo_root: Path = REPO_ROOT,
) -> dict[Path, str]:
    models = discover_sqla_symbols(ring_dir, repo_root)
    verify_api_classes_are_models(
        models, discover_api_classes(ring_dir, repo_root)
    )
    jobs = discover_job_modules(ring_dir, repo_root)
    search = discover_search_functions(ring_dir, repo_root)
    factories = discover_factories(factories_dir, repo_root)
    paths = {
        MODELS_PATH: render_models(models),
        JOBS_PATH: render_jobs(jobs),
        SEARCH_PATH: render_search(search),
        FACTORIES_PATH: render_factories(factories),
    }
    return {
        path: format_generated(source, path) for path, source in paths.items()
    }


def write_generated_imports(
    ring_dir: Path = RING_DIR,
    factories_dir: Path = FACTORIES_DIR,
    repo_root: Path = REPO_ROOT,
) -> list[Path]:
    written: list[Path] = []
    for path, source in generated_files(
        ring_dir, factories_dir, repo_root
    ).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        written.append(path)
    return written


def check_generated_imports(
    ring_dir: Path = RING_DIR,
    factories_dir: Path = FACTORIES_DIR,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Return a unified diff if generated files are stale, else ``\"\"``."""
    diffs: list[str] = []
    for path, source in generated_files(
        ring_dir, factories_dir, repo_root
    ).items():
        existing = path.read_text() if path.is_file() else ""
        if existing == source:
            continue
        diffs.append(
            "".join(
                difflib.unified_diff(
                    existing.splitlines(keepends=True),
                    source.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            )
        )
    return "".join(diffs)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    check = "--check" in args
    if check:
        diff = check_generated_imports()
        if diff:
            sys.stderr.write(
                "Generated import files are stale. "
                "Run `ring gen imports`.\n"
                f"{diff}"
            )
            return 1
        print("Generated import files are up to date.")
        return 0
    for path in write_generated_imports():
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
