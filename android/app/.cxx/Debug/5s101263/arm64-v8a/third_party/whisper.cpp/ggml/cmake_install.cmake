# Install script for directory: D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "C:/Program Files (x86)/asr_mobile")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Debug")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "0")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "TRUE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "D:/Android Studio/SDK/ndk/26.1.10909125/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-objdump.exe")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/.cxx/Debug/5s101263/arm64-v8a/third_party/whisper.cpp/ggml/src/cmake_install.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/.cxx/Debug/5s101263/arm64-v8a/third_party/whisper.cpp/ggml/src/libggml.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include" TYPE FILE FILES
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-cpu.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-alloc.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-backend.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-blas.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-cann.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-cpp.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-cuda.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-opt.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-metal.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-rpc.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-virtgpu.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-sycl.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-vulkan.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-webgpu.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-zendnn.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/ggml-openvino.h"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/src/main/cpp/third_party/whisper.cpp/ggml/include/gguf.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/.cxx/Debug/5s101263/arm64-v8a/third_party/whisper.cpp/ggml/src/libggml-base.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/ggml" TYPE FILE FILES
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/.cxx/Debug/5s101263/arm64-v8a/third_party/whisper.cpp/ggml/ggml-config.cmake"
    "D:/959/shu/上大/Machine_learn/ASR Mobile/android/app/.cxx/Debug/5s101263/arm64-v8a/third_party/whisper.cpp/ggml/ggml-version.cmake"
    )
endif()

