#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-sanitize"

SANITIZERS="${DATA_BRIDGE_SANITIZERS:-address,undefined}"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDATA_BRIDGE_SANITIZERS="${SANITIZERS}"

if command -v nproc >/dev/null 2>&1; then
  JOBS="$(nproc)"
else
  JOBS="$(sysctl -n hw.ncpu || echo 4)"
fi

cmake --build "${BUILD_DIR}" -- -j"${JOBS}"
ctest --test-dir "${BUILD_DIR}" --output-on-failure
