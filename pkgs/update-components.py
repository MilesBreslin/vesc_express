#!/usr/bin/env python3
"""Refresh the component locks and archive hashes using ESP-IDF's Python env."""

import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen
from ruamel.yaml import YAML

from idf_component_manager.dependencies import download_project_dependencies
from idf_component_tools.build_system_tools import get_idf_version
from idf_component_tools.lock import LockManager
from idf_component_tools.manager import ManifestManager
from idf_component_tools.registry.storage_client import StorageClient
from idf_component_tools.utils import ProjectRequirements


def main():
    root = Path(__file__).resolve().parent.parent
    version = get_idf_version()
    if version != "5.5.4":
        raise SystemExit(f"Expected ESP-IDF 5.5.4, got {version}")

    pins = {"idfVersion": version, "sources": {}, "targets": {}}
    registry = StorageClient("https://components-file.espressif.com/")
    with tempfile.TemporaryDirectory(prefix="vesc-components-") as directory:
        for target in ("esp32c3", "esp32c6", "esp32s3", "esp32p4"):
            os.environ["IDF_TARGET"] = target
            work = Path(directory) / target
            work.mkdir()
            lock = work / "dependencies.lock"
            requirements = ProjectRequirements([
                ManifestManager(str(root / "main"), "main").load()
            ])
            download_project_dependencies(requirements, str(lock), str(work / "components"))
            solution = LockManager(str(lock)).load()
            pins["targets"][target] = YAML(typ="safe").load(lock.read_text())
            for component in solution.dependencies:
                if not component.source.downloadable:
                    continue
                key = f"{component.name}@{component.version}"
                if key in pins["sources"]:
                    continue
                url = registry.component(component.name, str(component.version))["download_url"]
                with urlopen(url) as response:
                    digest = hashlib.file_digest(response, "sha256").digest()
                pins["sources"][key] = {
                    "url": url,
                    "hash": "sha256-" + base64.b64encode(digest).decode(),
                }

    (root / "pkgs" / "components.json").write_text(
        json.dumps(pins, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
