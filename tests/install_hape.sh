#!/bin/bash
set -e
echo "Installing HAPE"

pip install --upgrade hape

echo
echo "hape v$(hape --version) installed successfully!"
echo