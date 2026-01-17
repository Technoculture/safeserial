#!/usr/bin/env python3
"""
Data Bridge - Universal CLI (bridge.py)

A single entry point for all project tasks: building, testing, verifying, and visualizing.

Usage:
    python bridge.py build          # Build C++, Python, Node
    python bridge.py test verify    # Run reliability verification (defaults to C++ target)
    python bridge.py test chaos     # Run interactive chaos visualizer (Live UI)
    python bridge.py test unit      # Run C++ unit tests
    python bridge.py viz            # Generate charts from test data
    python bridge.py clean          # Clean all artifacts

    # Advanced Verification
    python scripts/verify_reliability.py --target node  # Verify Node.js bindings specificially
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR
BUILD_DIR = PROJECT_ROOT / "build"
NODE_DIR = PROJECT_ROOT / "bindings" / "node"
PYTHON_BINDING_DIR = PROJECT_ROOT / "bindings" / "python"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# --- Colors ---
GREEN = "\033[92m" if sys.platform != "win32" or os.environ.get("TERM") else ""
YELLOW = "\033[93m" if sys.platform != "win32" or os.environ.get("TERM") else ""
RED = "\033[91m" if sys.platform != "win32" or os.environ.get("TERM") else ""
BLUE = "\033[94m" if sys.platform != "win32" or os.environ.get("TERM") else ""
NC = "\033[0m" if sys.platform != "win32" or os.environ.get("TERM") else ""


def log(msg: str):
    print(f"{GREEN}[BRIDGE]{NC} {msg}")


def warn(msg: str):
    print(f"{YELLOW}[WARN]{NC} {msg}")


def error(msg: str):
    print(f"{RED}[ERROR]{NC} {msg}")
    sys.exit(1)


def info(msg: str):
    print(f"{BLUE}[INFO]{NC} {msg}")


def get_cpu_count() -> int:
    try:
        return os.cpu_count() or 4
    except:
        return 4


def run(
    cmd: list[str], cwd: Path = PROJECT_ROOT, check: bool = True, title: str = None
) -> bool:
    """Run a command with optional title logging."""
    if title:
        info(title)

    cmd_str = " ".join(cmd)
    # print(f"DEBUG: Executing '{cmd_str}' in {cwd}") # Verbose debug

    try:
        subprocess.run(cmd, cwd=cwd, check=check)
        return True
    except subprocess.CalledProcessError as e:
        if check:
            error(f"Command failed: {cmd_str}\n{e}")
        return False
    except FileNotFoundError:
        warn(f"Command not found: {cmd[0]}")
        return False
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)


def uv_run(args: list[str], cwd: Path = PROJECT_ROOT):
    """Run a command using 'uv run' within the python binding project context."""
    uv = shutil.which("uv")
    if not uv:
        error("'uv' is required but not found in PATH.")

    cmd = [uv, "run", "--project", str(PYTHON_BINDING_DIR)] + args
    run(cmd, cwd=cwd, check=True)


# --- Tasks ---


def task_build(args):
    """Build everything."""
    log("Building C++ Library...")
    BUILD_DIR.mkdir(exist_ok=True)

    # C++ CMake
    cmake_args = ["cmake", ".."]
    sanitizers = os.environ.get("DATA_BRIDGE_SANITIZERS", "").strip()
    if sanitizers:
        cmake_args.append(f"-DDATA_BRIDGE_SANITIZERS={sanitizers}")

    coverage = os.environ.get("DATA_BRIDGE_COVERAGE", "").strip()
    if coverage:
        cmake_args.append(f"-DDATA_BRIDGE_COVERAGE={coverage}")

    fuzzing = os.environ.get("DATA_BRIDGE_ENABLE_FUZZING", "").strip()
    if fuzzing:
        cmake_args.append(f"-DDATA_BRIDGE_ENABLE_FUZZING={fuzzing}")

    if not run(cmake_args, cwd=BUILD_DIR, title="Configuring CMake"):
        error("CMake configure failed")

    # C++ Build
    if sys.platform == "win32":
        run(
            [
                "cmake",
                "--build",
                ".",
                "--config",
                "Release",
                "-j",
                str(get_cpu_count()),
            ],
            cwd=BUILD_DIR,
            title="Compiling C++",
        )
    else:
        run(["make", f"-j{get_cpu_count()}"], cwd=BUILD_DIR, title="Compiling C++")

    # Node Bindings
    if NODE_DIR.exists() and (NODE_DIR / "package.json").exists():
        log("Building Node.js Bindings...")
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        run(
            [npm, "install"],
            cwd=NODE_DIR,
            check=False,
            title="Installing Node Dependencies",
        )
        run(
            [npm, "run", "build"],
            cwd=NODE_DIR,
            check=False,
            title="Building Node Addon",
        )
    else:
        warn("Node bindings skipped (not found)")

    # Python Bindings
    log("Building Python Environment...")
    prep_sdist = PYTHON_BINDING_DIR / "scripts" / "prepare_sdist.py"
    run(
        [sys.executable, str(prep_sdist)],
        cwd=PROJECT_ROOT,
        title="Preparing Python sdist sources",
    )
    uv_run(["pip", "install", "-e", "."], cwd=PYTHON_BINDING_DIR)

    log("Build Complete!")


def task_test(args):
    """Run tests."""
    target = args.target
    artifacts_dir = PROJECT_ROOT / "docs" / "traceability" / "artifacts" / "latest"

    def run_logged(cmd: list[str], log_path: Path, cwd: Path, title: str, check: bool):
        info(title)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as log_file:
            start = datetime.utcnow().isoformat() + "Z"
            log_file.write(f"=== START {start} ===\n")
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    ts = datetime.utcnow().isoformat() + "Z"
                    log_file.write(f"[{ts}] {line}")
                proc.wait()
                end = datetime.utcnow().isoformat() + "Z"
                log_file.write(f"=== END {end} (exit {proc.returncode}) ===\n")
                if check and proc.returncode != 0:
                    error(f"Command failed: {' '.join(cmd)}")
                return proc.returncode == 0
            except subprocess.CalledProcessError as e:
                if check:
                    error(f"Command failed: {' '.join(cmd)}\n{e}")
                return False
            except FileNotFoundError:
                warn(f"Command not found: {cmd[0]}")
                return False
            except KeyboardInterrupt:
                print("\nInterrupted.")
                sys.exit(130)

    # Unit Tests
    if target == "unit" or target == "all":
        log("=== Unit Tests ===")
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # 1. C++
        ctest = shutil.which("ctest")
        if ctest:
            run_logged(
                [ctest, "--output-on-failure"],
                artifacts_dir / "ctest.log",
                BUILD_DIR,
                "C++ Core Tests",
                True,
            )
        else:
            warn("ctest not found")

        # 2. Python
        log("Python Tests...")
        pytest_log = artifacts_dir / "pytest.log"
        pytest_junit = artifacts_dir / "pytest-junit.xml"
        uv_run(
            [
                "python",
                "-m",
                "pytest",
                "--log-file",
                str(pytest_log),
                "--log-file-level",
                "INFO",
                "--log-format",
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                "--log-date-format",
                "%Y-%m-%dT%H:%M:%S",
                "--junitxml",
                str(pytest_junit),
            ],
            cwd=PYTHON_BINDING_DIR,
        )

        # 3. Node.js
        if NODE_DIR.exists():
            log("Node.js Tests...")
            npm = "npm.cmd" if sys.platform == "win32" else "npm"
            run_logged(
                [npm, "test"],
                artifacts_dir / "node-test.log",
                NODE_DIR,
                "Node.js Tests",
                False,
            )

    # Reliability/System Tests
    if target == "verify" or target == "all":
        print()
        log("=== System Verification ===")
        print("Running Reliability Verification Suite (ISO Claim)...")
        script = SCRIPTS_DIR / "verify_reliability.py"
        # Using uv with matplotlib for plotting
        uv_cmd = ["--with", "matplotlib", "python", str(script)]
        uv_run(uv_cmd, cwd=PROJECT_ROOT)

        viz_report = (
            PROJECT_ROOT
            / "docs"
            / "traceability"
            / "artifacts"
            / "latest"
            / "verify_reliability_report.md"
        )
        viz = SCRIPTS_DIR / "visualize_results.py"
        uv_run(
            ["--with", "matplotlib", "python", str(viz), str(viz_report)],
            cwd=PROJECT_ROOT,
        )

        diagram = SCRIPTS_DIR / "generate_diagram.py"
        uv_run(["--with", "matplotlib", "python", str(diagram)], cwd=PROJECT_ROOT)

        linker = SCRIPTS_DIR / "link_test_ids.py"
        run(
            [sys.executable, str(linker)],
            cwd=PROJECT_ROOT,
            title="Linking TestIDs",
        )

        traceability = SCRIPTS_DIR / "validate_traceability.py"
        run(
            [sys.executable, str(traceability)],
            cwd=PROJECT_ROOT,
            title="Validating Traceability",
        )

        artifacts = SCRIPTS_DIR / "collect_artifacts.py"
        run(
            [sys.executable, str(artifacts)],
            cwd=PROJECT_ROOT,
            title="Collecting Verification Artifacts",
        )

    if target == "chaos":
        log("Launching Interactive Chaos Visualizer...")
        script = SCRIPTS_DIR / "chaos_visual.py"
        # Pass through any extra args to the visualizer
        extra_args = args.extra_args if hasattr(args, "extra_args") else []
        cmd = ["--with", "rich", "python", str(script)] + extra_args
        uv_run(cmd, cwd=PROJECT_ROOT)

    if target == "coverage":
        log("=== Coverage ===")
        run(["bash", str(SCRIPTS_DIR / "run_coverage.sh")], cwd=PROJECT_ROOT)

    if target == "fuzz":
        log("=== Fuzzing ===")
        run(["bash", str(SCRIPTS_DIR / "run_fuzz.sh")], cwd=PROJECT_ROOT)


def task_viz(args):
    """Generate reports/charts."""
    log("Running Visualization...")
    script = SCRIPTS_DIR / "visualize_results.py"
    report_file = (
        PROJECT_ROOT
        / "docs"
        / "traceability"
        / "artifacts"
        / "latest"
        / "verify_reliability_report.md"
    )

    if not report_file.exists():
        warn(
            "No verify_reliability_report.md found. Run 'bridge.py test verify' first."
        )

    # We pass the log file path if needed, but the script defaults to test_report.md logic
    # Actually the script takes the report file as arg 1
    cmd = ["--with", "matplotlib", "python", str(script), str(report_file)]
    uv_run(cmd, cwd=PROJECT_ROOT)


def task_clean(args):
    """Clean artifacts."""
    log("Cleaning Project...")

    dirs = [
        BUILD_DIR,
        NODE_DIR / "build",
        NODE_DIR / "node_modules",
        PROJECT_ROOT / ".pytest_cache",
        PROJECT_ROOT / "__pycache__",
    ]

    files = [
        PROJECT_ROOT / "test_report.md",
        PROJECT_ROOT / "combined.log",
        PROJECT_ROOT / "chaos_monkey.log",
        PROJECT_ROOT / "test_timeline.png",
        PROJECT_ROOT / "reliability_plot.png",
        PROJECT_ROOT / "docs" / "test_report.md",
        PROJECT_ROOT / "docs" / "test_timeline.png",
        PROJECT_ROOT / "docs" / "reliability_plot.png",
    ]

    for d in dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            info(f"Removed {d}")

    for f in files:
        if f.exists():
            f.unlink()
            info(f"Removed {f}")

    log("Clean Complete.")


def task_publish(args):
    """Publish packages to PyPI and NPM."""
    target = args.target
    uv = shutil.which("uv")
    if not uv:
        error("'uv' is required but not found in PATH.")

    # Python
    if target == "python" or target == "all":
        log("Publishing Python Bindings...")
        # Clean dist
        dist_dir = PYTHON_BINDING_DIR / "dist"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)

        prep_sdist = PYTHON_BINDING_DIR / "scripts" / "prepare_sdist.py"
        run(
            [sys.executable, str(prep_sdist)],
            cwd=PROJECT_ROOT,
            title="Preparing Python sdist sources",
        )

        # Build sdist and wheel
        # Note: 'uv build' must be run directly, not via 'uv run'
        run([uv, "build"], cwd=PYTHON_BINDING_DIR, title="Building Python Package")

        # Publish
        log("Uploading to PyPI...")
        # Note: Requires UV_PUBLISH_TOKEN or interactive login
        run([uv, "publish"], cwd=PYTHON_BINDING_DIR, title="Publishing to PyPI")

    # Node
    if target == "node" or target == "all":
        if NODE_DIR.exists():
            log("Publishing Node.js Bindings...")
            npm = "npm.cmd" if sys.platform == "win32" else "npm"
            # Access public is usually required for scoped packages (@org/pkg)
            # Requires npm login beforehand
            run(
                [npm, "publish", "--access", "public"],
                cwd=NODE_DIR,
                title="NPM Publish",
            )
        else:
            warn("Node bindings not found, skipping publish")

    log("Publish Complete!")


# --- Main CLI ---


def main():
    parser = argparse.ArgumentParser(
        description="DataBridge Universal Tool (bridge.py)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Build
    parser_build = subparsers.add_parser(
        "build", help="Build all components (C++, Node, Python env)"
    )

    # Test
    parser_test = subparsers.add_parser("test", help="Run tests")
    parser_test.add_argument(
        "target",
        choices=["unit", "verify", "chaos", "coverage", "fuzz", "all"],
        default="all",
        nargs="?",
        help="Test target: unit (C++), verify (Automated Suite), chaos (Interactive UI)",
    )
    parser_test.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to underlying tool (e.g. for chaos)",
    )

    # Viz
    parser_viz = subparsers.add_parser("viz", help="Generate result visualizations")

    # Clean
    parser_clean = subparsers.add_parser("clean", help="Clean build artifacts")

    # Publish
    parser_pub = subparsers.add_parser("publish", help="Publish packages to PyPI/NPM")
    parser_pub.add_argument(
        "target",
        choices=["python", "node", "all"],
        default="all",
        nargs="?",
        help="Target registry",
    )

    args = parser.parse_args()

    if args.command == "build":
        task_build(args)
    elif args.command == "test":
        task_test(args)
    elif args.command == "viz":
        task_viz(args)
    elif args.command == "clean":
        task_clean(args)
    elif args.command == "publish":
        task_publish(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
