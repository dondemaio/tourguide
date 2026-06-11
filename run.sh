#!/bin/bash

set -eu -o pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
declare -r SCRIPT_DIR

export PYTHONPATH=src
source "${SCRIPT_DIR}/.venv/bin/activate"
python src/main.py
