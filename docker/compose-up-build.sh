#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
declare -r SCRIPT_DIR

cd "${SCRIPT_DIR}/../" || exit 123

docker compose -f "${SCRIPT_DIR}/tourguide.yml" -f "${SCRIPT_DIR}/tourguide-dev.yml" up --build -d
