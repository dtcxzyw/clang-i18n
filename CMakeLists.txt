cmake_minimum_required(VERSION 3.12)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_FIND_PACKAGE_SORT_ORDER NATURAL)
set(CMAKE_FIND_PACKAGE_SORT_DIRECTION DEC)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

project(clang-i18n)

find_package(LLVM REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
message(STATUS "LLVM include dir: ${LLVM_INCLUDE_DIRS}")
include_directories(${LLVM_INCLUDE_DIRS})

find_package(Clang REQUIRED CONFIG)
include_directories(${CLANG_INCLUDE_DIRS})
message(STATUS "Clang include dir: ${CLANG_INCLUDE_DIRS}")

include_directories(${CMAKE_CURRENT_BINARY_DIR})

add_library(clang-i18n MODULE clang-i18n.cpp)
target_compile_definitions(clang-i18n PRIVATE -DCLANG_I18N_CLANG_SUPPORT)
add_library(llvm-i18n MODULE clang-i18n.cpp)

target_link_libraries(clang-i18n PRIVATE dl)
if (LLVM_LINK_LLVM_DYLIB)
  if (NOT CLANG_LINK_CLANG_DYLIB)
    message(FATAL_ERROR "Cannot set CLANG_LINK_CLANG_DYLIB=OFF when "
                        "LLVM_LINK_LLVM_DYLIB=ON")
  endif()
  target_compile_definitions(clang-i18n PRIVATE -DCLANG_I18N_LINK_DYLIB)
  if(NOT DEFINED LLVM_SHLIB_SYMBOL_VERSION)
    # "Symbol version prefix for libLLVM.so and libclang-cpp.so"
    set(LLVM_SHLIB_SYMBOL_VERSION "LLVM_${LLVM_VERSION_MAJOR}.${LLVM_VERSION_MINOR}")
  endif()
  message(STATUS "LLVM_SHLIB_SYMBOL_VERSION: ${LLVM_SHLIB_SYMBOL_VERSION}")
  configure_file(simple_version_script.map.in simple_version_script.map)
  target_link_libraries(clang-i18n PRIVATE clang-cpp LLVM)
  target_link_options(clang-i18n PRIVATE -Wl,--version-script,${CMAKE_CURRENT_BINARY_DIR}/simple_version_script.map)
  target_link_libraries(llvm-i18n PRIVATE LLVM)
  target_link_options(llvm-i18n PRIVATE -Wl,--version-script,${CMAKE_CURRENT_BINARY_DIR}/simple_version_script.map)
else()
  if (CLANG_LINK_CLANG_DYLIB)
    message(FATAL_ERROR "Cannot set CLANG_LINK_CLANG_DYLIB=ON when "
                        "LLVM_LINK_LLVM_DYLIB=OFF")
  endif()
  target_link_libraries(clang-i18n PRIVATE clangBasic LLVMSupport LLVMOption)
  target_link_libraries(llvm-i18n PRIVATE LLVMSupport LLVMOption)
endif()

include(GNUInstallDirs)

set(CLANG_I18N_DATADIR ${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n CACHE PATH "Installation path for translation files")

install(TARGETS clang-i18n
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  COMPONENT clang-i18n
)
install(TARGETS llvm-i18n
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  COMPONENT clang-i18n
)
install(DIRECTORY i18n
  DESTINATION ${CLANG_I18N_DATADIR}
  COMPONENT clang-i18n
  FILES_MATCHING PATTERN "*.yml"
)

configure_file(config.h.in config.h)
