#! /bin/bash

source_dir=./src
build_dir=./build-MeshGenerator
install_dir=.


# Make the build directory if it doesn't exist
if [ ! -d "$build_dir" ]; then
	mkdir "$build_dir"
fi


# Configure cmake
echo ""
echo "----------------------------------------------------------------"
echo "CONFIGURING CMAKE..."
echo "----------------------------------------------------------------"
cmake -S $source_dir -B $build_dir

# Build project
echo ""
echo "----------------------------------------------------------------"
echo "BUILDING THE PROJECT..."
echo "----------------------------------------------------------------"
cmake --build $build_dir

# Install project
echo ""
echo "----------------------------------------------------------------"
echo "INSTALLING THE PROJECT..."
echo "----------------------------------------------------------------"
cmake --install $build_dir --prefix $install_dir