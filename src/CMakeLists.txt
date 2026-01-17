add_library(data_bridge STATIC
    protocol/crc16.cpp
    data_bridge.cpp
    resilient_bridge.cpp
)

data_bridge_apply_sanitizers(data_bridge)

# Platform specific sources
if(WIN32)
    target_sources(data_bridge PRIVATE transport/platform/windows/windows_serial.cpp)
else()
    target_sources(data_bridge PRIVATE transport/platform/linux/linux_serial.cpp)
endif()

target_include_directories(data_bridge PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Export the library name for other subdirectories
set(DATA_BRIDGE_LIB data_bridge PARENT_SCOPE)
