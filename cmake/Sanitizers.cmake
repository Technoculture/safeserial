function(data_bridge_apply_sanitizers target_name)
  if(NOT DATA_BRIDGE_SANITIZERS)
    return()
  endif()

  if(MSVC)
    message(WARNING "Sanitizers are not supported with MSVC for target ${target_name}")
    return()
  endif()

  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    message(WARNING "Sanitizers are only supported with Clang/GCC for target ${target_name}")
    return()
  endif()

  string(TOLOWER "${DATA_BRIDGE_SANITIZERS}" sanitizer_list)
  string(REPLACE "," ";" sanitizer_list "${sanitizer_list}")
  string(REPLACE " " ";" sanitizer_list "${sanitizer_list}")

  list(REMOVE_ITEM sanitizer_list "")

  list(FIND sanitizer_list "thread" has_thread)
  list(FIND sanitizer_list "address" has_address)
  list(FIND sanitizer_list "leak" has_leak)
  if(has_thread GREATER -1 AND (has_address GREATER -1 OR has_leak GREATER -1))
    message(FATAL_ERROR "ThreadSanitizer cannot be combined with Address/Leak sanitizers")
  endif()

  string(JOIN "," sanitizer_flags ${sanitizer_list})
  target_compile_options(${target_name} PRIVATE -fsanitize=${sanitizer_flags} -fno-omit-frame-pointer)
  target_link_options(${target_name} PRIVATE -fsanitize=${sanitizer_flags})
endfunction()
