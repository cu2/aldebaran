#!/bin/bash -e
set -o pipefail

PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "${PARENT_DIR}"

if [ ! -d "virtualenv" ]; then
  echo 'Please install first by running ./scripts/setup.sh'
  exit 1
fi

. "virtualenv/bin/activate"

exec python -m unittest "$@"
