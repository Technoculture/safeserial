add_library(safeserial STATIC
    safeserial.cpp
    resilient_bridge.cpp
)

safeserial_apply_sanitizers(safeserial)

# Platform specific sources
if(WIN32)
    target_sources(safeserial PRIVATE transport/platform/windows/windows_serial.cpp)
else()
    target_sources(safeserial PRIVATE transport/platform/linux/linux_serial.cpp)
endif()

target_include_directories(safeserial PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Export the library name for other subdirectories
set(SAFESERIAL_LIB safeserial PARENT_SCOPE)
