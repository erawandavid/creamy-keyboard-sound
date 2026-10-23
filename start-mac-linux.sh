#!/bin/sh
# Start creamy keyboard sounds. Press Ctrl+C (or close the terminal) to stop.
cd "$(dirname "$0")" || exit 1

if [ ! -f .venv/installed ]; then
    echo "First run: setting things up, this takes a minute..."
    rm -rf .venv
    if ! python3 -m venv .venv; then
        echo "Python 3 is needed: https://www.python.org/downloads/"
        rm -rf .venv
        exit 1
    fi
    if ! .venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt; then
        echo "Installing failed. Check your internet connection and run this again."
        rm -rf .venv
        exit 1
    fi
    touch .venv/installed
fi

exec .venv/bin/python -m creamy_keys "$@"
