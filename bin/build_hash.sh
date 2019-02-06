#!/bin/bash

find misc/ docker/ subset/ -type f | sort | xargs sha1sum | sha256sum | awk '{print $1}'
