cmake_minimum_required(VERSION 3.15)
project(safeserial_node)

set(CMAKE_CXX_STANDARD 17)

# Check for bundled dependencies (NPM package mode)
set(LOCAL_DEPS "${CMAKE_CURRENT_SOURCE_DIR}/deps")
if(EXISTS "${LOCAL_DEPS}/include")
    message(STATUS "Using bundled dependencies in ${LOCAL_DEPS}")
    set(PROJECT_ROOT "${LOCAL_DEPS}")
else()
    # Development mode (Monorepo)
    get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
    message(STATUS "Using development source root: ${PROJECT_ROOT}")
endif()

# Include Node-API headers
include_directories(${CMAKE_JS_INC})

# Platform-specific serial implementation
if(WIN32)
    set(PLATFORM_SOURCES
        ${PROJECT_ROOT}/src/transport/platform/windows/windows_serial.cpp
    )
else()
    set(PLATFORM_SOURCES
        ${PROJECT_ROOT}/src/transport/platform/linux/linux_serial.cpp
    )
endif()

# Build core library sources directly
set(CORE_SOURCES
    ${PROJECT_ROOT}/src/safeserial.cpp
    ${PROJECT_ROOT}/src/resilient_bridge.cpp
    ${PLATFORM_SOURCES}
)

# Build the native addon
add_library(${PROJECT_NAME} SHARED
    src/addon.cpp
    src/serial_wrapper.cpp
    ${CORE_SOURCES}
    ${CMAKE_JS_SRC}
)

# cmake-js supplies a node_api.def file for N-API builds on Windows, but MSVC
# still needs a node.lib import library materialized before the addon links.
if(WIN32 AND CMAKE_JS_NODELIB_DEF AND CMAKE_JS_NODELIB_TARGET)
    if(CMAKE_GENERATOR_PLATFORM MATCHES "ARM64|arm64")
        set(SAFESERIAL_NODE_LIB_MACHINE "ARM64")
    elseif(CMAKE_GENERATOR_PLATFORM MATCHES "Win32|x86|ia32")
        set(SAFESERIAL_NODE_LIB_MACHINE "X86")
    else()
        set(SAFESERIAL_NODE_LIB_MACHINE "X64")
    endif()

    add_custom_command(
        OUTPUT "${CMAKE_JS_NODELIB_TARGET}"
        COMMAND "${CMAKE_AR}"
            /def:${CMAKE_JS_NODELIB_DEF}
            /out:${CMAKE_JS_NODELIB_TARGET}
            /machine:${SAFESERIAL_NODE_LIB_MACHINE}
        DEPENDS "${CMAKE_JS_NODELIB_DEF}"
        VERBATIM
    )
    add_custom_target(safeserial_node_lib DEPENDS "${CMAKE_JS_NODELIB_TARGET}")
    add_dependencies(${PROJECT_NAME} safeserial_node_lib)
endif()

# Set properties for Node.js addon
set_target_properties(${PROJECT_NAME} PROPERTIES
    PREFIX ""
    SUFFIX ".node"
)

# Include paths
target_include_directories(${PROJECT_NAME} PRIVATE
    ${PROJECT_ROOT}/include
    ${CMAKE_JS_INC}
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    ${CMAKE_JS_LIB}
)

# Enable N-API version 8
target_compile_definitions(${PROJECT_NAME} PRIVATE
    NAPI_VERSION=8
    NODE_ADDON_API_DISABLE_DEPRECATED
)
