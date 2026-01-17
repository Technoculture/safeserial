add_executable(reliability_test reliability_test.cpp)
target_link_libraries(reliability_test PRIVATE safeserial)
safeserial_apply_sanitizers(reliability_test)

# Deep verification tests (requires GoogleTest)
if(POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)
endif()

include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(test_deep_verification test_deep_verification.cpp)
target_link_libraries(test_deep_verification PRIVATE safeserial GTest::gtest_main)
safeserial_apply_sanitizers(test_deep_verification)
add_test(NAME DeepVerification COMMAND test_deep_verification)

add_executable(test_crc32 test_crc32.cpp)
target_link_libraries(test_crc32 PRIVATE safeserial GTest::gtest_main)
safeserial_apply_sanitizers(test_crc32)
add_test(NAME CRC32 COMMAND test_crc32)

add_executable(test_safeserial test_safeserial.cpp)
target_link_libraries(test_safeserial PRIVATE safeserial GTest::gtest_main)
safeserial_apply_sanitizers(test_safeserial)
add_test(NAME SafeSerial COMMAND test_safeserial)

add_executable(test_resilient_bridge test_resilient_bridge.cpp)
target_link_libraries(test_resilient_bridge PRIVATE safeserial GTest::gtest_main)
safeserial_apply_sanitizers(test_resilient_bridge)
add_test(NAME ResilientBridge COMMAND test_resilient_bridge)

if(SAFESERIAL_ENABLE_FUZZING)
  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_executable(fuzz_packet fuzz_packet.cpp)
    target_link_libraries(fuzz_packet PRIVATE safeserial)
    target_compile_options(fuzz_packet PRIVATE -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer)
    target_link_options(fuzz_packet PRIVATE -fsanitize=fuzzer,address,undefined)
  else()
    message(WARNING "Fuzzing targets require Clang")
  endif()
endif()
