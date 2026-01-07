add_executable(serial_app cli_app.cpp)
target_link_libraries(serial_app PRIVATE data_bridge)
