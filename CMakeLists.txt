cmake_minimum_required(VERSION 2.8)
project(image-recog)
find_package(OpenCV REQUIRED)
add_executable(viking-vision viking-vision.cpp)
target_link_libraries(viking-vision ${OpenCV_LIBS})
<<<<<<< HEAD
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
=======
>>>>>>> 362f9a697b4701c6d79f0b5ed870223083b022b1
