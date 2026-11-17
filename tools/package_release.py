#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package this public collection without local build outputs or Git history."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from verify_release import main as verify

ROOT = Path(__file__).resolve().parent.parent
NAME = "Baroque-Instax-Frames-v0.1.0"


def main():
    verify()
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    target = out / (NAME + ".zip")
    folders = ["models", "renders", "concepts", "validation", "source", "tools",
               "docs", "photos", "LICENSES", ".github"]
    files = [ROOT / n for n in ["README.md", "LICENSE", "PROVENANCE.txt",
                               "CONTRIBUTING.md", "SHA256SUMS", ".gitignore", ".gitattributes"]]
    for folder in folders:
        files += [p for p in (ROOT / folder).rglob("*") if p.is_file()
                  and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".log"}]
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, NAME + "/" + path.relative_to(ROOT).as_posix())
    checksum = sha256(target.read_bytes()).hexdigest()
    (out / (target.name + ".sha256")).write_text(f"{checksum}  {target.name}\n")
    print(f"Created {target.name}: {target.stat().st_size:,} bytes, {len(files)} files")
    print(f"SHA256 {checksum}")


if __name__ == "__main__":
    main()
