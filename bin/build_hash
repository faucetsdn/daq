#!/bin/bash

ROOT=$(realpath $(dirname $0)/..)
build_files=$ROOT/.build_files
find misc/ docker/ subset/ -type f | sort | xargs sha1sum > $build_files
cat $build_files | sha256sum | awk '{print $1}'
