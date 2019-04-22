#!/usr/bin/env bash
set -eu
set -o pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

if [ ! -d "${ROOT_DIR}/virtualenv" ]; then
  echo 'Please install first by running ./scripts/setup.sh'
  exit 1
fi

. "${ROOT_DIR}/virtualenv/bin/activate"

exec python "${ROOT_DIR}/aldebaran.py" "$@"
