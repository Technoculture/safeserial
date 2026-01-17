#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-sanitize"

SANITIZERS="${DATA_BRIDGE_SANITIZERS:-address,undefined}"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDATA_BRIDGE_SANITIZERS="${SANITIZERS}"

cmake --build "${BUILD_DIR}" -- -j"$(sysctl -n hw.ncpu || echo 4)"
ctest --test-dir "${BUILD_DIR}" --output-on-failure
