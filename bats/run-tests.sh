#!/bin/bash

if ! command -v bats &> /dev/null; then
    echo "Bats framework is not installed. Install it using: sudo apt-get install bats"
    exit 1
fi

bats bats/hape_tests.bats
