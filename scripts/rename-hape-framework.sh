#!/bin/bash

read -p "Enter AppNameShort: " app_name_short
read -p "Enter AppNameLong: " app_name_long
read -p "Enter appname (lowercase): " appname

export LC_CTYPE=C
export LANG=C

find . -type f \( ! -path "*/.venv/*" ! -path "*/playground/*" \) -exec sh -c '
    iconv -f UTF-8 -t UTF-8 "{}" > /dev/null 2>&1 && sed -i "" "s/AppNameShort/$1/g" "{}"
' _ "$app_name_short" {} \;

find . -type f \( ! -path "*/.venv/*" ! -path "*/playground/*" \) -exec sh -c '
    iconv -f UTF-8 -t UTF-8 "{}" > /dev/null 2>&1 && sed -i "" "s/AppNameLong/$1/g" "{}"
' _ "$app_name_long" {} \;

find . -type f \( ! -path "*/.venv/*" ! -path "*/playground/*" \) -exec sh -c '
    iconv -f UTF-8 -t UTF-8 "{}" > /dev/null 2>&1 && sed -i "" "s/appname/$1/g" "{}"
' _ "$appname" {} \;

echo "Renaming complete."
