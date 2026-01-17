#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-coverage"
OUT_DIR="${ROOT_DIR}/docs/coverage"

cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDATA_BRIDGE_COVERAGE=ON

cmake --build "${BUILD_DIR}" -- -j"$(sysctl -n hw.ncpu || echo 4)"
ctest --test-dir "${BUILD_DIR}" --output-on-failure

mkdir -p "${OUT_DIR}"

if command -v gcovr >/dev/null 2>&1; then
  gcovr -r "${ROOT_DIR}" \
    --exclude "${ROOT_DIR}/build-coverage" \
    --xml-pretty -o "${OUT_DIR}/coverage.xml" \
    --html-details -o "${OUT_DIR}/index.html"
  echo "Coverage report written to ${OUT_DIR}/index.html"
else
  echo "gcovr not found; install it to generate coverage reports."
  echo "Raw coverage data is available in ${BUILD_DIR}."
fi
