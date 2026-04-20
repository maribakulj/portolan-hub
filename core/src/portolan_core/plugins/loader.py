"""Plugin loader.

Two discovery mechanisms coexist:

1. **Directory-based** — scan a filesystem path for `manifest.yaml` files.
   The plugin's own Python module is imported relative to the manifest
   directory (we prepend the directory to `sys.path` transiently). Used
   for in-repo plugins and for user-provided `PORTOLAN_PLUGINS_DIR`.
2. **Entry points** — read `importlib.metadata.entry_points(group='portolan.plugins')`.
   Used for pip-installed plugins. Each entry point resolves to a
   callable returning a `(Manifest, Connector)` pair, or to a class
   paired with a sibling manifest discovered via its package data.

One plugin failing must not break the others — errors are collected and
exposed via `PluginLoader.errors`.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from portolan_core.connector import Connector
from portolan_core.errors import ManifestError, PluginLoadError
from portolan_core.manifest import Manifest, load_manifest

log = structlog.get_logger(__name__)


@dataclass
class LoadFailure:
    """Non-fatal record of a plugin that failed to load."""

    location: str
    error: str
    code: str


@dataclass
class PluginLoader:
    """Stateful loader that accumulates successes and failures."""

    loaded: list[Connector] = field(default_factory=list)
    errors: list[LoadFailure] = field(default_factory=list)

    def load_from_directory(self, root: Path) -> None:
        """Scan `root` for `*/manifest.yaml` and load each."""
        if not root.exists():
            log.warning("plugins_dir_missing", path=str(root))
            return

        for manifest_path in sorted(root.glob("*/manifest.yaml")):
            try:
                connector = _load_single_from_directory(manifest_path)
            except (ManifestError, PluginLoadError) as exc:
                self.errors.append(
                    LoadFailure(
                        location=str(manifest_path),
                        error=str(exc),
                        code=getattr(exc, "code", "unknown"),
                    )
                )
                log.warning(
                    "plugin_load_failed",
                    path=str(manifest_path),
                    error=str(exc),
                )
                continue
            self.loaded.append(connector)
            log.info(
                "plugin_loaded",
                source_id=connector.source.id,
                path=str(manifest_path),
            )

    def load_from_entry_points(self, group: str = "portolan.plugins") -> None:
        """Load plugins advertised via `importlib.metadata.entry_points`."""
        for ep in importlib.metadata.entry_points(group=group):
            try:
                obj = ep.load()
                connector = _instantiate_entry_point(ep.name, obj)
            except (ManifestError, PluginLoadError) as exc:
                self.errors.append(
                    LoadFailure(
                        location=f"entry_point:{ep.name}",
                        error=str(exc),
                        code=getattr(exc, "code", "unknown"),
                    )
                )
                log.warning("plugin_load_failed", entry_point=ep.name, error=str(exc))
                continue
            self.loaded.append(connector)
            log.info(
                "plugin_loaded",
                source_id=connector.source.id,
                entry_point=ep.name,
            )


def _load_single_from_directory(manifest_path: Path) -> Connector:
    """Load a single directory-based plugin.

    The connector module is imported under a unique, plugin-scoped name
    (``portolan._plugins.<id>.<module>``) so that plugins that all call
    their module ``connector`` do not shadow each other in ``sys.modules``.
    """
    manifest = load_manifest(manifest_path)
    plugin_dir = manifest_path.parent

    module_name, _, class_name = manifest.entry_point.partition(":")
    if not module_name or not class_name:
        raise PluginLoadError(
            f"invalid entry_point {manifest.entry_point!r}: expected 'module:Class'"
        )

    module_file = plugin_dir / f"{module_name.replace('.', '/')}.py"
    if not module_file.is_file():
        raise PluginLoadError(
            f"entry_point module file not found: {module_file} (plugin dir: {plugin_dir})"
        )

    qualified = f"portolan._plugins.{manifest.id}.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified, module_file)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"could not build import spec for {module_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(qualified, None)
        raise PluginLoadError(f"error importing {module_file}: {exc}") from exc

    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise PluginLoadError(f"module {module_file} has no attribute {class_name!r}") from exc

    if not isinstance(cls, type) or not issubclass(cls, Connector):
        raise PluginLoadError(f"{manifest.entry_point!r} does not resolve to a Connector subclass")

    return _instantiate_connector(manifest, cls)


def _resolve_entry_point(dotted: str) -> type[Connector]:
    """Import ``module:Class`` and return the class (for entry_points path)."""
    module_name, _, class_name = dotted.partition(":")
    if not module_name or not class_name:
        raise PluginLoadError(f"invalid entry_point {dotted!r}: expected 'module:Class'")
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise PluginLoadError(f"cannot import {module_name!r}: {exc}") from exc
    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise PluginLoadError(f"module {module_name!r} has no attribute {class_name!r}") from exc
    if not isinstance(cls, type) or not issubclass(cls, Connector):
        raise PluginLoadError(f"{dotted!r} does not resolve to a Connector subclass")
    return cls


def _instantiate_connector(manifest: Manifest, cls: type[Connector]) -> Connector:
    try:
        return cls(source=manifest.to_source())
    except Exception as exc:
        raise PluginLoadError(f"connector {cls.__name__!r} failed to instantiate: {exc}") from exc


def _instantiate_entry_point(ep_name: str, obj: object) -> Connector:
    """Coerce whatever the entry point returned into a Connector.

    We accept:
      - a `Connector` instance, ready to use ;
      - a callable returning one ;
      - a class whose `.manifest` attribute points to a manifest file ;
    Anything else is rejected.
    """
    if isinstance(obj, Connector):
        return obj

    if callable(obj):
        candidate = obj()
        if isinstance(candidate, Connector):
            return candidate
        if isinstance(candidate, type) and issubclass(candidate, Connector):
            cls = candidate
        else:
            raise PluginLoadError(
                f"entry point {ep_name!r} callable must return a Connector "
                f"or Connector subclass, got {type(candidate).__name__}"
            )
    elif isinstance(obj, type) and issubclass(obj, Connector):
        cls = obj
    else:
        raise PluginLoadError(
            f"entry point {ep_name!r} resolved to {type(obj).__name__}, "
            "expected Connector instance, callable, or subclass"
        )

    manifest_attr = getattr(cls, "manifest_path", None)
    if manifest_attr is None:
        raise PluginLoadError(
            f"entry point {ep_name!r} class {cls.__name__!r} has no `manifest_path` "
            "attribute; cannot derive a Source"
        )

    manifest = load_manifest(Path(str(manifest_attr)))
    return _instantiate_connector(manifest, cls)


def load_plugins_from_directory(root: Path) -> tuple[list[Connector], list[LoadFailure]]:
    """One-shot helper returning `(connectors, failures)`."""
    loader = PluginLoader()
    loader.load_from_directory(root)
    return loader.loaded, loader.errors


def load_plugins_from_entry_points(
    group: str = "portolan.plugins",
) -> tuple[list[Connector], list[LoadFailure]]:
    loader = PluginLoader()
    loader.load_from_entry_points(group=group)
    return loader.loaded, loader.errors
