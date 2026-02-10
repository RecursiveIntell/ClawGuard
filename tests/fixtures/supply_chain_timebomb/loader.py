"""Plugin loader for code metrics analysis."""

import importlib
import urllib.request
import types


# Plugin registry URL - loads analysis modules from remote server
PLUGIN_REGISTRY = "https://metrics-plugins.example.com/registry/v2"


def load_remote_plugin(plugin_name: str) -> types.ModuleType:
    """Load an analysis plugin from the remote registry."""
    plugin_url = f"{PLUGIN_REGISTRY}/{plugin_name}.py"
    response = urllib.request.urlopen(plugin_url)
    source_code = response.read().decode("utf-8")

    # Create module from remote source and execute it
    module = types.ModuleType(plugin_name)
    exec(compile(source_code, plugin_url, "exec"), module.__dict__)
    return module


def load_all_plugins() -> list[types.ModuleType]:
    """Load all registered analysis plugins."""
    registry_url = f"{PLUGIN_REGISTRY}/manifest.json"
    response = urllib.request.urlopen(registry_url)
    import json
    manifest = json.loads(response.read().decode("utf-8"))

    plugins = []
    for plugin_info in manifest.get("plugins", []):
        plugin = load_remote_plugin(plugin_info["name"])
        plugins.append(plugin)
    return plugins


def analyze_file(filepath: str) -> dict:
    """Run all loaded plugins against a source file."""
    plugins = load_all_plugins()
    results = {}
    for plugin in plugins:
        if hasattr(plugin, "analyze"):
            results[plugin.__name__] = plugin.analyze(filepath)
    return results
