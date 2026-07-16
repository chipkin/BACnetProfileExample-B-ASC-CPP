# =============================================================================
# CMake build for the BACnet B-ASC (Application Specific Controller) C++ example.
#
# This example links the CAS BACnet Stack by COMPILING IT FROM SOURCE: it builds
# every file in the stack's source/ folder straight into the executable and
# calls the stack's C API (CASBACnetStackDLL.h) directly. There is no DLL/.so to
# build, copy, or ship first - everything compiles into one self-contained
# executable.
#
# NOTE: the first build compiles the entire stack (~600 source files), so it
# takes a few minutes. Subsequent incremental builds are fast.
#
# Build:
#   cmake -B build -S .
#   cmake --build build --config Release
# Run (from the example folder):
#   ./build/BACnetExampleBASC          (Linux/macOS)
#   .\build\Release\BACnetExampleBASC.exe   (Windows)
# =============================================================================

cmake_minimum_required(VERSION 3.15)
project(BACnetProfileExample_CPP_B_ASC CXX C)


# Default to a Release build.
#
# Without this, a single-config generator (Unix Makefiles / Ninja - the default
# on Linux and macOS) leaves CMAKE_BUILD_TYPE EMPTY, and the documented
# `cmake --build build --config Release` is SILENTLY IGNORED there: --config
# only means anything to a multi-config generator like Visual Studio. The result
# is that the whole stack (~600 files) compiles at -O0 and the customer never
# finds out. Windows is unaffected, which is exactly why this survived so long.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Locate the pieces this project ships -----------------------------------
# The shared helper is vendored into this repository at ./common.
if(NOT DEFINED EXAMPLES_COMMON_DIR)
    set(EXAMPLES_COMMON_DIR "${CMAKE_CURRENT_SOURCE_DIR}/common")
endif()

# The CAS BACnet Stack is a git submodule of this repository, at
# ./submodules/cas-bacnet-stack. Run `git submodule update --init --recursive`
# after cloning. (Override with -D CAS_STACK_DIR=... to use a stack elsewhere.)
if(NOT DEFINED CAS_STACK_DIR)
    set(CAS_STACK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/submodules/cas-bacnet-stack")
endif()
set(CAS_STACK_SOURCE_DIR "${CAS_STACK_DIR}/source")

if(NOT EXISTS "${CAS_STACK_SOURCE_DIR}/CASBACnetStackDLL.h")
    message(FATAL_ERROR
        "CAS BACnet Stack source not found at: ${CAS_STACK_SOURCE_DIR}\n"
        "The stack is a git submodule. After cloning this repository, run:\n"
        "    git submodule update --init --recursive\n"
        "Or pass -D CAS_STACK_DIR=/path/to/cas-bacnet-stack to use a stack elsewhere.")
endif()

# --- Gather the CAS BACnet Stack source -------------------------------------
# Compiling from source: grab every .cpp/.c in the stack's source/ folder. The
# example calls the stack's C API (CASBACnetStackDLL.h) directly, so no adapter
# layer is needed.
file(GLOB CAS_STACK_SOURCES
    "${CAS_STACK_SOURCE_DIR}/*.cpp"
    "${CAS_STACK_SOURCE_DIR}/*.c")

# --- The shared example helper ----------------------------------------------
set(COMMON_SOURCES
    "${EXAMPLES_COMMON_DIR}/CASExampleHelper.cpp"
    "${EXAMPLES_COMMON_DIR}/SimpleUDP.cpp")

# --- The executable ---------------------------------------------------------
add_executable(BACnetExampleBASC
    main.cpp
    ${COMMON_SOURCES}
    ${CAS_STACK_SOURCES})

target_include_directories(BACnetExampleBASC PRIVATE
    "${EXAMPLES_COMMON_DIR}"
    "${CAS_STACK_SOURCE_DIR}")

# --- Warnings on OUR sources only -------------------------------------------
# Apply strict warnings to the example + helper sources, but NOT to the bundled
# third-party stack (~600 files) which would be noisy and isn't ours to fix.
if(MSVC)
    set(EXAMPLE_WARNINGS "/W4")
else()
    set(EXAMPLE_WARNINGS "-Wall;-Wextra")
endif()
set_source_files_properties(main.cpp ${COMMON_SOURCES}
    PROPERTIES COMPILE_OPTIONS "${EXAMPLE_WARNINGS}")

# --- Platform sockets -------------------------------------------------------
# ws2_32  = Winsock (UDP); iphlpapi = GetAdaptersInfo (local broadcast address).
if(WIN32)
    target_link_libraries(BACnetExampleBASC PRIVATE ws2_32 iphlpapi)
endif()
