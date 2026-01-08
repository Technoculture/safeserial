add_executable(reliability_test reliability_test.cpp)
target_link_libraries(reliability_test PRIVATE data_bridge)

# Deep verification tests (requires GoogleTest)
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(test_deep_verification test_deep_verification.cpp)
target_link_libraries(test_deep_verification PRIVATE data_bridge GTest::gtest_main)
add_test(NAME DeepVerification COMMAND test_deep_verification)

add_executable(test_crc16 test_crc16.cpp)
target_link_libraries(test_crc16 PRIVATE data_bridge GTest::gtest_main)
add_test(NAME CRC16 COMMAND test_crc16)
