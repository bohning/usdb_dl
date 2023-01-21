#!/bin/bash

VERSION=3.10
python=$1

function CheckPythonCommandVersion {
    found=$($1 --version 2>/dev/null)
    [[ $found = Python" "$VERSION.* ]] && return 0
    return 1
}

if [ "$python" ]; then
    if ! CheckPythonCommandVersion "$python"; then
        echo "'$python' is not a valid Python interpreter!"
        exit 1
    fi
else
    if CheckPythonCommandVersion "py -3.10"; then
        python=py
    elif CheckPythonCommandVersion python; then
        python=python
    elif CheckPythonCommandVersion python3; then
        python=python3
    else
        echo No valid Python interpreter found!
        exit 1
    fi
fi

$python -m venv venv
source venv/bin/activate
$python -m pip install --upgrade pip tox
pip install -e '.[dev]'
