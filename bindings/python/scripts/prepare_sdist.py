#!/usr/bin/env python3
"""
Sync top-level C++ sources/headers into bindings/python for sdist builds.
"""

import shutil
from pathlib import Path


def sync_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    bindings_root = project_root / "bindings" / "python"

    include_src = project_root / "include"
    src_src = project_root / "src"

    include_dest = bindings_root / "include_cpp"
    src_dest = bindings_root / "src_cpp"

    if not include_src.exists():
        raise SystemExit(f"Missing include dir: {include_src}")
    if not src_src.exists():
        raise SystemExit(f"Missing src dir: {src_src}")

    include_dest.parent.mkdir(parents=True, exist_ok=True)
    sync_tree(include_src, include_dest)
    sync_tree(src_src, src_dest)
    print(f"Prepared sdist sources in {bindings_root}")


if __name__ == "__main__":
    main()
