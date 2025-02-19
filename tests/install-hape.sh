#!/bin/bash
set -e

echo "Installing hape cli"

echo "\$ pip install --upgrade hape"
pip install --upgrade hape
echo "hape v$(hape --version) installed successfully!"