#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check archived print projects and their reports using only the standard library.

This checks release integrity and packaging, not physical fit or fresh slicing.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def metadata(element):
    return {x.get("key"): x.get("value") for x in element.findall("metadata")}


def check_project(path, report):
    require(sha256(path.read_bytes()).hexdigest() == report["sha256"],
            f"{path.name}: SHA-256 differs from the sliced file")
    require(report["return_code"] == 0 and report["plates"] == 2,
            f"{path.name}: missing successful two-plate slicer record")
    require(report["filament_changes"] == [1, 0], f"{path.name}: color transitions")
    require(not any(report["warning_messages"]), f"{path.name}: slicer warning")
    with ZipFile(path) as archive:
        require(archive.testzip() is None, f"{path.name}: corrupt ZIP entry")
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        require(model.get("unit") == "millimeter", f"{path.name}: units")
        require(len(model.findall("m:build/m:item", NS)) == 2,
                f"{path.name}: expected two physical objects")
        plates = config.findall("plate")
        require([metadata(x).get("plater_id") for x in plates] == ["1", "2"],
                f"{path.name}: plate numbering")
        require([metadata(x.find("model_instance")).get("object_id") for x in plates]
                == ["3", "5"], f"{path.name}: plate/object mapping")
        part_colors = {p.get("id"): metadata(p).get("extruder")
                       for p in config.findall("object/part")}
        require(part_colors == {"1": "1", "2": "2", "4": "1"},
                f"{path.name}: white/black/back assignments")
        require(len(settings["filament_colour"]) == 2, f"{path.name}: two filaments")
        for number in (1, 2, 4):
            mesh = ET.fromstring(archive.read(f"3D/Objects/object_{number}.model"))
            vertices = mesh.findall(".//m:vertex", NS)
            triangles = mesh.findall(".//m:triangle", NS)
            require(bool(vertices) and bool(triangles), f"{path.name}: empty mesh {number}")
            require(all(0 <= int(t.get(k)) < len(vertices)
                        for t in triangles for k in ("v1", "v2", "v3")),
                    f"{path.name}: invalid mesh indices {number}")
        for name in archive.namelist():
            if name.endswith((".model", ".xml", ".config")):
                data = archive.read(name)
                require(b"/Users/" not in data and b"/tmp/" not in data,
                        f"{path.name}: machine-specific path in {name}")


def check_links():
    # Check repository-relative Markdown links/images, including README galleries.
    for doc in ROOT.rglob("*.md"):
        if any(x in {".git", ".venv", "build", "dist"} for x in doc.relative_to(ROOT).parts):
            continue
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", doc.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            require((doc.parent / target).exists(), f"{doc.relative_to(ROOT)}: missing {target}")


def main():
    reports = json.loads((ROOT / "validation/slicer-summary.json").read_text())
    require(len(reports) == 7, "expected six frame reports and one coupon")
    files = {x.name for x in (ROOT / "models").glob("*.3mf")}
    require(files == {x["file"] for x in reports}, "model/report filenames differ")
    manifest = {line.split()[1]: line.split()[0]
                for line in (ROOT / "SHA256SUMS").read_text().splitlines() if line.strip()}
    require(manifest == {"models/" + r["file"]: r["sha256"] for r in reports},
            "SHA256SUMS differs from the archived slicer records")
    for report in sorted(reports, key=lambda x: x["file"]):
        path = ROOT / "models" / report["file"]
        key = path.stem.removesuffix("-Instax-Mini-3-Magnets")
        individual = json.loads((ROOT / "validation" / (key + "-slicer.json")).read_text())
        require(report == individual, f"{path.name}: summary/report mismatch")
        check_project(path, report)
        if key != "PLA-Clip-Fit-Test":
            geometry = json.loads((ROOT / "validation" / (key + "-geometry.json")).read_text())
            require(geometry["watertight_parts"] and geometry["full_film_concealed"]
                    and geometry["back_projection_hidden"] and geometry["closed_socket_roofs_checked"],
                    f"{path.name}: incomplete archived geometry checks")
            require(len(geometry["magnet_centers_mm"]) == 3, f"{path.name}: three magnets")
        print("PASS", path.name)
    designs = json.loads((ROOT / "source/designs-final.json").read_text())
    require(len(designs) == 6, "expected six design records")
    for design in designs:
        require((ROOT / design["generated_path"]).is_file(), f"missing concept: {design['id']}")
        for reference in design["generation_inputs"]:
            require((ROOT / reference).is_file(), f"missing reference: {reference}")
    check_links()
    print("PASS catalog assets and local documentation links")
    print("Integrity checks passed. Physical fit and durability remain untested.")


if __name__ == "__main__":
    main()
