#!/bin/bash

source ./activate
echo "Run tests:"
nosetests

echo "Testing Examples"
set -e # all errors result in failure
echo "Test Simple Example:"
cd examples/simple
export MYGLOBALSCRATCH_DIR="$(pwd)/scratch/global"
export MYLOCALSCRATCH_DIR="$(pwd)/scratch/local"
yes "y" | configJob -x JobConfig.ini