#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-fuzz"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDATA_BRIDGE_ENABLE_FUZZING=ON \
  -DDATA_BRIDGE_SANITIZERS=address,undefined

if command -v nproc >/dev/null 2>&1; then
  JOBS="$(nproc)"
else
  JOBS="$(sysctl -n hw.ncpu || echo 4)"
fi

cmake --build "${BUILD_DIR}" -- -j"${JOBS}"

if [[ -x "${BUILD_DIR}/tests/fuzz_packet" ]]; then
  "${BUILD_DIR}/tests/fuzz_packet" -runs=10000
else
  echo "Fuzz target not built. Ensure Clang is used."
  exit 1
fi
