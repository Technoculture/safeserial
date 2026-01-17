cmake_minimum_required(VERSION 3.15)
project(safeserial_sdk_python LANGUAGES CXX)

find_package(pybind11 REQUIRED CONFIG)

# Define source location relative to this file.
# Prefer generated sdist sources when present, otherwise fall back to repo root.
set(INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include_cpp")
set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src_cpp")
if(NOT EXISTS "${SRC_DIR}")
    set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../src")
endif()
if(NOT EXISTS "${INCLUDE_DIR}")
    set(INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../include")
endif()

# Determine platform source
if(WIN32)
    set(SERIAL_SRC "${SRC_DIR}/transport/platform/windows/windows_serial.cpp")
else()
    set(SERIAL_SRC "${SRC_DIR}/transport/platform/linux/linux_serial.cpp")
endif()

# Bindings module
pybind11_add_module(_core
    src/safeserial/_core.cpp
    "${SRC_DIR}/safeserial.cpp"
    "${SRC_DIR}/resilient_bridge.cpp"
    ${SERIAL_SRC}
)

target_include_directories(_core PRIVATE ${INCLUDE_DIR})

# Set C++ standard
target_compile_features(_core PRIVATE cxx_std_17)

# Install the module to the safeserial package directory
install(TARGETS _core DESTINATION safeserial)
