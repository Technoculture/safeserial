#!/usr/bin/env python3
"""
Data Bridge - Cross-Platform Build and Test Script

Usage:
    python scripts/build.py         # Build everything
    python scripts/build.py test    # Build and run all tests
    python scripts/build.py clean   # Clean build artifacts
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
BUILD_DIR = PROJECT_ROOT / "build"
NODE_DIR = PROJECT_ROOT / "bindings" / "node"

# Colors (ANSI, works on most terminals)
GREEN = "\033[92m" if sys.platform != "win32" or os.environ.get("TERM") else ""
YELLOW = "\033[93m" if sys.platform != "win32" or os.environ.get("TERM") else ""
RED = "\033[91m" if sys.platform != "win32" or os.environ.get("TERM") else ""
NC = "\033[0m" if sys.platform != "win32" or os.environ.get("TERM") else ""


def log(msg: str):
    print(f"{GREEN}[BUILD]{NC} {msg}")


def warn(msg: str):
    print(f"{YELLOW}[WARN]{NC} {msg}")


def error(msg: str):
    print(f"{RED}[ERROR]{NC} {msg}")
    sys.exit(1)


def run(cmd: list[str], cwd: Path = PROJECT_ROOT, check: bool = True) -> bool:
    """Run a command and return success status."""
    try:
        subprocess.run(cmd, cwd=cwd, check=check)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        warn(f"Command not found: {cmd[0]}")
        return False


def get_cpu_count() -> int:
    try:
        return os.cpu_count() or 4
    except:
        return 4


def build_cpp():
    """Build the C++ library using CMake."""
    log("Building C++ library...")
    BUILD_DIR.mkdir(exist_ok=True)
    
    # CMake configure
    if not run(["cmake", ".."], cwd=BUILD_DIR):
        error("CMake configuration failed")
    
    # Build
    if sys.platform == "win32":
        # Windows: use cmake --build
        if not run(["cmake", "--build", ".", "--config", "Release", "-j", str(get_cpu_count())], cwd=BUILD_DIR):
            error("C++ build failed")
    else:
        # Unix: use make
        if not run(["make", f"-j{get_cpu_count()}"], cwd=BUILD_DIR):
            error("C++ build failed")
    
    log(f"C++ build complete: {BUILD_DIR}")


def build_node():
    """Build Node.js bindings."""
    log("Building Node.js bindings...")
    
    if not NODE_DIR.exists():
        warn("Node bindings directory not found, skipping")
        return
    
    package_json = NODE_DIR / "package.json"
    if not package_json.exists():
        warn("No package.json in node bindings, skipping")
        return
    
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    
    run([npm, "install"], cwd=NODE_DIR, check=False)
    run([npm, "run", "build"], cwd=NODE_DIR, check=False)
    
    log("Node.js bindings build complete")


def test_cpp():
    """Run C++ tests."""
    log("Running C++ tests...")
    
    ctest = shutil.which("ctest")
    if ctest:
        run([ctest, "--output-on-failure"], cwd=BUILD_DIR, check=False)
    
    log("C++ tests complete")


def test_node():
    """Run Node.js tests."""
    log("Running Node.js tests...")
    
    if not NODE_DIR.exists():
        return
    
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    run([npm, "test"], cwd=NODE_DIR, check=False)
    
    log("Node.js tests complete")


def test_python():
    """Run Python verification suite."""
    log("Running Python verification suite...")
    
    uv = shutil.which("uv")
    python = sys.executable
    
    test_script = PROJECT_ROOT / "tests" / "verification_suite.py"
    if not test_script.exists():
        warn("verification_suite.py not found")
        return
    
    if uv:
        run([uv, "run", "--with", "matplotlib", "python", str(test_script)], check=False)
    else:
        run([python, str(test_script)], check=False)
    
    log("Python tests complete")


def clean():
    """Remove all build artifacts."""
    log("Cleaning build artifacts...")
    
    dirs_to_remove = [
        BUILD_DIR,
        NODE_DIR / "build",
        NODE_DIR / "node_modules",
    ]
    
    files_to_remove = list(PROJECT_ROOT.glob("*.log")) + \
                      list(PROJECT_ROOT.glob("*.png")) + \
                      [PROJECT_ROOT / "test_report.md"]
    
    for d in dirs_to_remove:
        if d.exists():
            shutil.rmtree(d)
            log(f"Removed {d}")
    
    for f in files_to_remove:
        if f.exists():
            f.unlink()
    
    log("Clean complete")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "build"
    
    if command == "build":
        build_cpp()
        build_node()
        log("All builds complete!")
    
    elif command == "test":
        build_cpp()
        build_node()
        print()
        log("=== Running Tests ===")
        test_cpp()
        test_node()
        test_python()
        print()
        log("All tests complete!")
    
    elif command == "clean":
        clean()
    
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
