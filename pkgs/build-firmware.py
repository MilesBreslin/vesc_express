#!/usr/bin/env python3
"""Build a selected firmware bundle inside the Nix build directory."""

import json
import os
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

# The upstream script owns hardware discovery and artifact collection.
sys.path.insert(0, str(Path.cwd()))
from build_all import build_target, get_hw_configs


def main():
    requested = json.loads(os.environ["boardsJSON"])
    configs = get_hw_configs()
    if requested != "all":
        unknown = set(requested) - {config["name"] for config in configs}
        if unknown:
            raise SystemExit(f"Unknown HW_NAME values: {', '.join(sorted(unknown))}")
        configs = [config for config in configs if config["name"] in requested]
    if not configs:
        raise SystemExit("No hardware configurations selected")

    pins = json.loads(Path(os.environ["componentPins"]).read_text())
    archives = json.loads(os.environ["componentSourcesJSON"])
    output = Path("build_output")
    shutil.rmtree(output, ignore_errors=True)
    resource = ET.Element("RCC")
    entries = ET.SubElement(resource, "qresource", prefix="/res/firmwares_esp/")
    for index, config in enumerate(configs, 1):
        # sdkconfig survives idf.py set-target/fullclean in some workflows.
        # Always reset it, including when only the flash/PSRAM variant changes.
        for directory in ("build", "managed_components"):
            shutil.rmtree(directory, ignore_errors=True)
        for filename in ("sdkconfig", "sdkconfig.old", "dependencies.lock"):
            Path(filename).unlink(missing_ok=True)

        target = config["target"].split("_", 1)[0]
        lock = pins["targets"][target]
        Path("dependencies.lock").write_text(json.dumps(lock))
        for name, component in lock["dependencies"].items():
            if name == "idf":
                continue
            destination = Path("managed_components") / name.replace("/", "__")
            destination.mkdir(parents=True)
            key = f"{name}@{component['version']}"
            with ZipFile(archives[key]) as archive:
                archive.extractall(destination)
            (destination / ".component_hash").write_text(component["component_hash"])

        if not build_target(config, str(output), idx=index, total=len(configs)):
            raise SystemExit(f"Firmware build failed: {config['name']}")
        for filename in ("bootloader.bin", "partition-table.bin", "vesc_express.bin"):
            relative = Path(target) / config["name"] / filename
            if (output / relative).stat().st_size == 0:
                raise SystemExit(f"Empty firmware artifact: {relative}")
            ET.SubElement(entries, "file").text = relative.as_posix()

    ET.indent(resource)
    ET.ElementTree(resource).write(output / "res_fw.qrc", encoding="unicode")


if __name__ == "__main__":
    main()
